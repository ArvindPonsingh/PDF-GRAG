from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_triplet_to_neo4j(tx, subject, predicate, object):
    tx.run(
        """
        MERGE (s:Entity {name: $subject})
        MERGE (o:Entity {name: $object})
        MERGE (s)-[:RELATION {type: $predicate}]->(o)
        """,
        subject=subject,
        predicate=predicate,
        object=object
    )

# You might want to add a function to clear the graph for testing purposes
def clear_neo4j_graph(driver):
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))
        print("Neo4j graph cleared.")