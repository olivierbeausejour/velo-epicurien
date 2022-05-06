from flask import Flask, jsonify, render_template
from py2neo import Graph
from pymongo import MongoClient

app = Flask(__name__)

MONGO_CLIENT = MongoClient('mongodb://root:password@mongodb:27017/')
MONGO_DB = MONGO_CLIENT.parcoursvelo
RESTAURANTS = MONGO_DB.restaurants

NEO4J_URL = "neo4j://neo4j"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_CLIENT = Graph(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD), secure=False)

two_ways_segments = NEO4J_CLIENT.run("MATCH (bp1:BikewayPoint)-[j1:joins]->(bp2:BikewayPoint)-[j2:joins]->(bp1) WHERE ID(j1) < ID(j2) RETURN bp1,bp2").data()
one_way_segments = NEO4J_CLIENT.run("MATCH (bp1:BikewayPoint)-[j:joins]->(bp2:BikewayPoint) WHERE NOT (bp2)-[:joins]->(bp1) RETURN bp1,bp2").data()
all_segments = one_way_segments + two_ways_segments

@app.route("/")
def home():
    restaurants = [r for r in RESTAURANTS.find()]
    return render_template('index.html', restaurants=restaurants, segments=all_segments)

@app.route("/heartbeat")
def get_selected_city():
    return jsonify({"villeChoisie": "Québec"})

@app.route('/restaurants')
def list_restaurants():
    restaurants = [r for r in RESTAURANTS.find()]
    return jsonify({"restaurants": restaurants})

@app.route("/extracted_data")
def get_extracted_data():
    try:
        restaurants = [r for r in RESTAURANTS.find()]
        bikeways = list(NEO4J_CLIENT.run("MATCH (bp:BikewayPoint) UNWIND bp.bikeway_ids as ids RETURN collect(DISTINCT ids)"))[0][0]

        return jsonify({"nbRestaurants": len(restaurants), "nbSegments": len(bikeways)})
    except Exception:
        return render_template("db_loading.html")

@app.route("/transformed_data")
def get_transformed_data():
    try:
        restaurants_types = [r for r in RESTAURANTS.aggregate([
            {"$unwind": "$cuisine"},
            {"$group": {"_id": "$cuisine", "count": {"$sum": 1}}},
            {"$replaceRoot": {"newRoot": {"$arrayToObject": [[{"k": "$_id", "v": "$count"}]]}}}])]

        types = dict((t, count) for restaurant_type in restaurants_types for t, count in restaurant_type.items())  
        two_way_bikeway_length = NEO4J_CLIENT.run("MATCH (bp1:BikewayPoint)-[j1:joins]->(bp2:BikewayPoint)-[j2:joins]->(bp1) WHERE ID(j1) < ID(j2) RETURN sum(j1.distance)").evaluate()
        one_way_bikeway_length = NEO4J_CLIENT.run("MATCH (bp1:BikewayPoint)-[j:joins]->(bp2:BikewayPoint) WHERE NOT (bp2)-[:joins]->(bp1) RETURN sum(j.distance)").evaluate()
        total_bikeway_length = two_way_bikeway_length + one_way_bikeway_length

        return jsonify({"restaurants": types, "longueurCyclable": total_bikeway_length})
    except Exception:
        return render_template("db_loading.html")