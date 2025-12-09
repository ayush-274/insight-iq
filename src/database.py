from sqlalchemy import create_engine, text, inspect
import os

# Using SQLite for dev; easy to swap for Postgres later
DB_URI = "sqlite:///chinook.db"

engine = create_engine(DB_URI)

def get_schema():
    """Returns a dictionary of Table Name -> List of Columns"""
    inspector = inspect(engine)
    schema_info = {}
    
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema_info[table_name] = [col['name'] for col in columns]
        
    return schema_info

def run_query(sql_query):
    """Executes a SQL query safely and returns results"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text(sql_query))
            return result.fetchall()
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    # TEST CODE
    print("🔍 Inspecting Database Schema...")
    schema = get_schema()
    print(f"Found {len(schema)} tables: {list(schema.keys())}")
    
    print("\n🧪 Testing Query: 'Top 3 Albums'")
    sample_data = run_query("SELECT Title FROM Album LIMIT 3;")
    print(sample_data)