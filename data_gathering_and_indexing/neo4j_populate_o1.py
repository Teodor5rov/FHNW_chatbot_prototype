import os
import json
import hashlib
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")

JSON_DIR = 'json_files_with_summaries'
CHUNKED_PAGES_DIR = 'chunked_pages'

BASE_URL = "https://www.fhnw.ch"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def create_graph():
    counter = 0

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        constraints = session.run("SHOW CONSTRAINTS")
        for record in constraints:
            constraint_name = record["name"]
            session.run(f"DROP CONSTRAINT {constraint_name}")

        indexes = session.run("SHOW INDEXES")
        for record in indexes:
            index_name = record["name"]
            session.run(f"DROP INDEX {index_name}")
        
        for json_filename in os.listdir(JSON_DIR):
            if json_filename.endswith('.json'):
                json_path = os.path.join(JSON_DIR, json_filename)
                with open(json_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    url_path = data.get('url_path', '').strip()
                    file_name = data.get('file_name', '').strip()
                    summary = data.get('summary', '').strip()

                    full_url = f"{BASE_URL}{url_path}"
                    
                    dir_name = os.path.splitext(file_name)[0]
                    chunks_dir = os.path.join(CHUNKED_PAGES_DIR, dir_name)
                    if os.path.exists(chunks_dir):
                        number_of_chunks = len([
                            f for f in os.listdir(chunks_dir)
                            if os.path.isfile(os.path.join(chunks_dir, f))
                        ])
                    else:
                        number_of_chunks = 0
                    
                    summary_hash = hashlib.sha256(summary.encode('utf-8')).hexdigest()[:8]

                    page_id = f"p_{number_of_chunks}_{summary_hash}_{counter}"

                    counter += 1
                    
                    session.run(
                        """
                        MERGE (p:Page {file_name: $file_name})
                        SET p.url = $url, p.summary = $summary, p.page_id = $page_id, p.number_of_chunks = $number_of_chunks
                        """,
                        file_name=file_name,
                        url=full_url,
                        summary=summary,
                        page_id=page_id,
                        number_of_chunks=number_of_chunks
                    )
                    
        for json_filename in os.listdir(JSON_DIR):
            if json_filename.endswith('.json'):
                json_path = os.path.join(JSON_DIR, json_filename)
                with open(json_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    file_name = data.get('file_name', '').strip()
                    dir_name = os.path.splitext(file_name)[0]
                    chunks_dir = os.path.join(CHUNKED_PAGES_DIR, dir_name)
                    if os.path.exists(chunks_dir):
                        for chunk_file_name in os.listdir(chunks_dir):
                            chunk_path = os.path.join(chunks_dir, chunk_file_name)
                            if os.path.isfile(chunk_path):
                                with open(chunk_path, 'r', encoding='utf-8') as chunk_file:
                                    chunk_content = chunk_file.read()
                                
                                chunk_number = int(os.path.splitext(chunk_file_name)[0].split('_')[-1])

                                chunk_hash = hashlib.sha256(chunk_content.encode('utf-8')).hexdigest()[:8]

                                chunk_id = f"c_{chunk_hash}_{counter}"

                                counter += 1

                                session.run(
                                    """
                                    MATCH (p:Page {file_name: $file_name})
                                    CREATE (c:Chunk {content: $content, chunk_id: $chunk_id, chunk_number: $chunk_number})
                                    CREATE (p)-[:HAS_CHUNK]->(c)
                                    """,
                                    file_name=file_name,
                                    content=chunk_content,
                                    chunk_id=chunk_id,
                                    chunk_number=chunk_number
                                )
                    else:
                        print(f"Warning: Chunks directory not found for {file_name}")
        
        for json_filename in os.listdir(JSON_DIR):
            if json_filename.endswith('.json'):
                json_path = os.path.join(JSON_DIR, json_filename)
                with open(json_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    file_name = data.get('file_name', '').strip()
                    links = data.get('links', [])
                    
                    for link_file_name in links:
                        link_file_name = link_file_name.strip()
                        session.run(
                            """
                            MATCH (from:Page {file_name: $from_file_name})
                            MATCH (to:Page {file_name: $to_file_name})
                            MERGE (from)-[:LINKS_TO]->(to)
                            """,
                            from_file_name=file_name,
                            to_file_name=link_file_name
                        )
    print("Graph creation completed.")

if __name__ == "__main__":
    create_graph()
    driver.close()
