import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.database import get_schema, run_query
from src.vector_db import get_relevant_tables
import time

# 1. Load Secrets
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. System Prompts
BASE_PROMPT = """
You are an expert Data Scientist and SQL developer.
Your task is to convert the user's natural language question into a valid SQL query for a SQLite database.

Here is the Database Schema:
{schema}

Rules:
1. Return ONLY the raw SQL code. Do not wrap it in markdown.
2. If the question cannot be answered, return "ERROR: Cannot answer".
3. Use READ-ONLY queries (SELECT).
"""

ERROR_PROMPT = """
The SQL query you generated caused an error.
Original Question: {question}
Your SQL: {sql}
Error Message: {error}

Task: Correct the SQL query to fix the error. Return ONLY the fixed SQL.
"""

def clean_sql(text):
    return text.replace("```sql", "").replace("```", "").strip()

def ask_data(question):
    print(f"\n🚀 DEBUG: Entering ask_data with question: {question}")
    
    # Check 1: Does the DB file exist?
    if not os.path.exists("chinook.db"):
        print("❌ DEBUG: chinook.db NOT FOUND in current directory!")
        return "Error: Database file not found on server."
    else:
        print("✅ DEBUG: chinook.db found.")

    # --- RAG LAYER ---
    print("📚 DEBUG: Calling Vector DB...")
    try:
        # We put this in try/except to catch Chroma hanging
        relevant_table_names = get_relevant_tables(question, n_results=5)
        print(f"🎯 DEBUG: RAG returned: {relevant_table_names}")
    except Exception as e:
        print(f"❌ DEBUG: RAG Failed: {e}")
        relevant_table_names = []
    
    # SAFETY FALLBACK
    if not relevant_table_names:
        print("⚠️ DEBUG: RAG returned empty. Using ALL tables.")
        relevant_table_names = list(get_schema().keys())
    
    # Schema Setup
    print("📝 DEBUG: Building Schema String...")
    full_schema = get_schema()
    filtered_schema = {k: v for k, v in full_schema.items() if k in relevant_table_names}
    
    schema_str = ""
    for table, info in filtered_schema.items():
        schema_str += f"Table: {table}\nColumns: {', '.join(info)}\n\n"
    
    # Prompt Setup
    current_prompt = BASE_PROMPT.format(schema=schema_str) + f"\nUser Question: {question}"
    
    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        print(f"⏳ DEBUG: Starting Gemini Attempt {attempt+1}...")
        sql_query = "UNKNOWN_SQL"
        
        try:
            # Hit Gemini
            print("🤖 DEBUG: Sending request to Gemini...")
            response = model.generate_content(current_prompt)
            print("✅ DEBUG: Gemini Responded.")
            
            sql_query = clean_sql(response.text)
            print(f"📝 DEBUG: SQL Generated: {sql_query}")
            
            if "ERROR" in sql_query:
                return "❌ AI could not understand the question."

            # Run Query
            print("💾 DEBUG: Running SQL on DB...")
            results = run_query(sql_query)
            print(f"✅ DEBUG: Query finished. Result type: {type(results)}")
            
            if isinstance(results, str) and results.startswith("Error"):
                raise Exception(results)
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ DEBUG: Attempt Failed: {error_msg}")
            print("💤 DEBUG: Sleeping 2s...")
            time.sleep(2)
            
            if sql_query == "UNKNOWN_SQL":
                attempt += 1
                continue 

            current_prompt = ERROR_PROMPT.format(
                question=question,
                sql=sql_query,
                error=error_msg
            )
            attempt += 1
    
    print("❌ DEBUG: All attempts failed.")
    return "❌ Failed to generate valid SQL after 3 attempts."

# --- TEST AREA ---
if __name__ == "__main__":
    answer = ask_data("Show me the top 3 Customer names who spent the most money.")
    print(answer)