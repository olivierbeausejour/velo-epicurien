# import numpy as np

# def coord_to_cartesian(lat, long):
#     lat, long = np.deg2rad(lat), np.deg2rad(long)

#     RADIUS = 6371000 # Earth radius in meters
#     x = RADIUS * np.cos(lat) * np.cos(long)
#     y = RADIUS * np.cos(lat) * np.sin(long)

#     return x,y

# def get_distance_from_segment():
#     p1 = coord_to_cartesian(46.81635, -71.20430)
#     p2 = coord_to_cartesian(46.81630, -71.20393)
#     p3 = coord_to_cartesian(46.81626, -71.20403)

#     print(np.abs((p2[0]-p1[0]) * (p1[1]-p3[1]) - (p1[0]-p3[0]) * (p2[1]-p1[1])) / (np.sqrt((p2[0]-p1[0]) * (p2[0]-p1[0]) + (p2[1]-p1[1]) * (p2[1]-p1[1]))))

# get_distance_from_segment()

from py2neo import Graph

NEO4J_URL = "neo4j://neo4j"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_CLIENT = Graph(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD), secure=False)

two_ways_segments = list(NEO4J_CLIENT.run("MATCH (bp1:BikewayPoint)-[j1:joins]->(bp2:BikewayPoint)-[j2:joins]->(bp1) WHERE ID(j1) < ID(j2) RETURN j1"))
pass