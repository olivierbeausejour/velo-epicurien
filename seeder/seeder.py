from py2neo import Graph
from pymongo import MongoClient
import json
import shutil
import os

NEO4J_URL = "neo4j://neo4j"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_CLIENT = Graph(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD), secure=False)

MONGODB_CLIENT = MongoClient('mongodb://root:password@mongodb:27017/')
MONGODB_DATABASE = MONGODB_CLIENT.parcoursvelo
RESTAURANTS_COLLECTION = MONGODB_DATABASE.restaurants

NEW_BIKEWAYS_PATH = "/data/new/bikeways"
ADDED_BIKEWAYS_PATH = "/data/added/bikeways"

NEW_RESTAURANTS_PATH = "/data/new/restaurants"
ADDED_RESTAURANTS_PATH = "/data/added/restaurants"

def transform_restaurant(restaurant):
    new_restaurant = {
        "_id": restaurant['id'].split('/')[1],
        "name": restaurant['properties']['name'],
        "cuisine": restaurant['properties']['cuisine'].split(';'),
        "geometry": restaurant['geometry']
    }
    
    return new_restaurant

def insert_restaurants():
    for file in os.scandir(NEW_RESTAURANTS_PATH):
        if file.path.endswith(".geojson") or file.path.endswith(".json"):   
            with open(file.path) as f:
                data = json.load(f)
                transformed_data = list(map(transform_restaurant, data))

                for restaurant in transformed_data:
                    RESTAURANTS_COLLECTION.replace_one({'_id': restaurant['_id']}, restaurant, upsert=True)

                    # Add to NEO4J for path calculations
                    NEO4J_CLIENT.run("""MATCH (resto:Restaurant) 
                                        WHERE resto.ID = {}
                                        DETACH DELETE resto""".format(restaurant['_id']))

                    NEO4J_CLIENT.run("""CREATE (:Restaurant 
                                        {{longitude:{}, latitude:{}, ID:{}, cuisine:{}}})""".format(
                                            restaurant['geometry']['coordinates'][0],
                                            restaurant['geometry']['coordinates'][1],
                                            restaurant['_id'],
                                            restaurant['cuisine']
                                            ))

                shutil.move(file.path, os.path.join(ADDED_RESTAURANTS_PATH, file.name))
    MONGODB_CLIENT.close()

def insert_bikeways():
    for file in os.scandir(NEW_BIKEWAYS_PATH):
        if file.path.endswith(".geojson") or file.path.endswith(".json"):   
            with open(file.path) as f:
                data = json.load(f)['features']
                pathways_data = [d for d in data if d['properties']['TYPE'] in ["Piste cyclable", "Chaussée désignée", "Bande cyclable"]]

                added_coordinates = dict()
                bikeway_points = []
                roads = []
                existing_bikeways_id = list(NEO4J_CLIENT.run("MATCH (bp:BikewayPoint) UNWIND bp.bikeway_ids as ids RETURN collect(DISTINCT ids)"))[0][0]

                for i, pathway in enumerate(pathways_data):
                    if pathway['properties']['ID'] in existing_bikeways_id:
                        # Delete node with its relationships if the current ID is the only one attached to it
                        NEO4J_CLIENT.run("""MATCH (bp:BikewayPoint) 
                                            WHERE {} IN bp.bikeway_ids AND size(bp.bikeway_ids) = 1
                                            DETACH DELETE bp""".format(pathway['properties']['ID']))

                        # Remove ID from node's bikeways IDs if the current ID is not the only one attached to it
                        NEO4J_CLIENT.run("""MATCH (bp:BikewayPoint) 
                                            WHERE {0} IN bp.bikeway_ids AND size(bp.bikeway_ids) > 1
                                            SET bp.bikeway_ids = [id IN bp.bikeways_ids WHERE id <> {0}]""".format(pathway['properties']['ID']))

                    one_way = True if pathway['properties']['DIRECTION_SENS_UNIQUE'] is not None else False
                    roads.append(([], one_way))

                    for location in pathway['geometry']['coordinates']:
                        c = (location[0], location[1])
                        if c not in added_coordinates.keys():
                            bikeway_points.append({
                                "longitude": location[0], 
                                "latitude": location[1], 
                                "bikeway_ids":[pathway['properties']['ID']]
                            })
                            added_coordinates.update({c:len(bikeway_points)-1})
                        else:
                            bikeway_point = bikeway_points[added_coordinates[c]]
                            bikeway_point["bikeway_ids"].append(pathway['properties']['ID'])

                        roads[i][0].append(c)
                    
                    if one_way and pathway['properties']['DIRECTION_SENS_UNIQUE'] == 'D':
                        roads[i][0].reverse()

                for point in bikeway_points:
                    NEO4J_CLIENT.run("""CREATE (:BikewayPoint {{longitude:{}, latitude:{}, bikeway_ids:{}}})""".format(
                                                                            point["longitude"], 
                                                                            point["latitude"],  
                                                                            point["bikeway_ids"]))

                for road in roads:
                    points = road[0]
                    for i in range(0, len(points)-1):
                        # Create one-way links between bikeway points in same segments
                        query = """MATCH (bp1:BikewayPoint), (bp2:BikewayPoint) 
                                            WHERE bp1.longitude = {} AND bp1.latitude = {} AND bp2.longitude = {} AND bp2.latitude = {}
                                            MERGE (bp1)-[:joins {{distance:distance(point({{longitude: bp1.longitude, latitude: bp1.latitude}}), 
                                            point({{longitude: bp2.longitude, latitude: bp2.latitude}}))}}]->(bp2)""".format(
                                                points[i][0],
                                                points[i][1], 
                                                points[i+1][0],
                                                points[i+1][1])
                        NEO4J_CLIENT.run(query)

                        if not road[1]:
                            query = """MATCH (bp1:BikewayPoint), (bp2:BikewayPoint) 
                                            WHERE bp1.longitude = {} AND bp1.latitude = {} AND bp2.longitude = {} AND bp2.latitude = {}
                                            MERGE (bp1)<-[:joins {{distance:distance(point({{longitude: bp1.longitude, latitude: bp1.latitude}}), 
                                            point({{longitude: bp2.longitude, latitude: bp2.latitude}}))}}]-(bp2)""".format(
                                                points[i][0],
                                                points[i][1], 
                                                points[i+1][0],
                                                points[i+1][1])

                            NEO4J_CLIENT.run(query)
                shutil.move(file.path, os.path.join(ADDED_BIKEWAYS_PATH, file.name))

if __name__ == "__main__":
    insert_restaurants()
    insert_bikeways()