import chromadb
from chromadb.utils import embedding_functions
from src.database import get_schema

# 1. Setup ChromaDB (Local Storage)
CHROMA_DATA_PATH = "chroma_data/"
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# Use a free, lightweight embedding model (runs locally)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create/Get Collection
collection = client.get_or_create_collection(
    name="schema_index",
    embedding_function=embed_fn
)

def index_schema():
    """Reads the DB schema and stores it in Vector DB"""
    print("📚 Indexing Database Schema into ChromaDB...")
    
    schema = get_schema() # Get Dict of Table -> Columns
    
    documents = [] # The text we search against
    metadatas = [] # Extra info (Table Name)
    ids = []       # Unique ID
    
    for table_name, columns in schema.items():
        # Create a "Description" for the table.
        # Ideally, you'd write these manually for better accuracy.
        # For now, we combine Table Name + Column Names.
        # Example: "Table Album contains columns: AlbumId, Title..."
        desc = f"Table {table_name} contains columns: {', '.join(columns)}"
        
        documents.append(desc)
        metadatas.append({"table_name": table_name})
        ids.append(table_name)
    
    # Add to ChromaDB
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"✅ Indexed {len(ids)} tables successfully!")

def get_relevant_tables(question, n_results=5):
    """Asks ChromaDB: 'Which tables are relevant to this question?'"""
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    # Extract table names from results
    relevant_tables = [meta['table_name'] for meta in results['metadatas'][0]]
    return relevant_tables

# --- Run Indexing Once ---
if __name__ == "__main__":
    index_schema()
    
    # Test Search
    q = "Who are the top selling artists?"
    tables = get_relevant_tables(q)
    print(f"\n🔎 Question: '{q}'")
    print(f"🎯 Relevant Tables: {tables}")