import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm
import time

load_dotenv()

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PERSIST_DIR = "./chroma_db"
BATCH_SIZE = 100

neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-large"
)

def get_neo4j_ids():
    with neo4j_driver.session() as session:
        pages = session.run("""
            MATCH (p:Page)
            RETURN p.page_id as id, p.summary as content
        """).data()
        
        chunks = session.run("""
            MATCH (p:Page)-[:HAS_CHUNK]->(c:Chunk)
            RETURN c.chunk_id as id, c.content as content, p.page_id as page_id
        """).data()
        
        return pages, chunks

def setup_chroma():
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    chunks_collection = client.get_or_create_collection(
        name="chunks",
        embedding_function=openai_ef
    )
    summaries_collection = client.get_or_create_collection(
        name="summaries",
        embedding_function=openai_ef
    )
    return client, chunks_collection, summaries_collection

def batch_items(items, batch_size):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def process_items(items, collection, item_type):
    for batch in tqdm(list(batch_items(items, BATCH_SIZE)), desc=f"Processing {item_type}"):
        ids = [str(item['id']) for item in batch]
        documents = [item['content'] for item in batch]
        params = {
            'ids': ids,
            'documents': documents
        }
        if item_type == 'chunks':
            metadatas = [{'page_id': item['page_id']} for item in batch]
            params['metadatas'] = metadatas
        try:
            collection.add(**params)
            time.sleep(1)
        except Exception as e:
            print(f"Error processing batch: {e}")
            continue

def main():
    try:
        print("Setting up ChromaDB...")
        client, chunks_collection, summaries_collection = setup_chroma()
        print("Retrieving items from Neo4j...")
        pages, chunks = get_neo4j_ids()
        print("Processing page summaries...")
        process_items(pages, summaries_collection, "summaries")
        print("Processing chunks...")
        process_items(chunks, chunks_collection, "chunks")
        print("\nVerification:")
        print(f"Summaries in ChromaDB: {summaries_collection.count()}")
        print(f"Chunks in ChromaDB: {chunks_collection.count()}")
        test_query = "example query"
        results = chunks_collection.query(
            query_texts=[test_query],
            n_results=2
        )
        print("\nExample query results:")
        for idx, (id, text, metadata) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['metadatas'][0]
        )):
            print(f"\nResult {idx + 1}:")
            print(f"ID: {id}")
            print(f"Text: {text[:100]}...")
            print(f"Metadata: {metadata}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        neo4j_driver.close()

if __name__ == "__main__":
    main()
