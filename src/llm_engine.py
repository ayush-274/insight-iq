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
    print(f"\n🤖 User Question: {question}")
    
    # --- RAG LAYER START ---
    print("📚 Consulting Vector DB...")
    
    relevant_table_names = get_relevant_tables(question, n_results=5)
    
    # ⚠️ SAFETY FALLBACK: If RAG fails, use ALL tables
    if not relevant_table_names:
        print("⚠️ RAG returned no results. Falling back to ALL tables.")
        relevant_table_names = list(get_schema().keys())
    else:
        print(f"🎯 Selected Tables: {relevant_table_names}")
    
    # Get full schema
    full_schema = get_schema()
    
    # Filter dictionary
    filtered_schema = {k: v for k, v in full_schema.items() if k in relevant_table_names}
    # --- RAG LAYER END ---
    
    # Format for Prompt
    schema_str = ""
    for table, info in filtered_schema.items():
        schema_str += f"Table: {table}\nColumns: {', '.join(info)}\n\n"
    
    # Initial Prompt
    current_prompt = BASE_PROMPT.format(schema=schema_str) + f"\nUser Question: {question}"
    
    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        print(f"⏳ Thinking... (Attempt {attempt+1}/{max_retries})")
        
        # --- FIX 1: Initialize variable here ---
        sql_query = "UNKNOWN_SQL" 
        
        try:
            # 1. Ask Gemini
            response = model.generate_content(current_prompt)
            sql_query = clean_sql(response.text)
            
            if "ERROR" in sql_query:
                return "❌ AI could not understand the question."

            print(f"📝 Generated SQL: {sql_query}")
            
            # 2. Run SQL
            # Note: run_query returns a dict {"columns": [], "data": []} OR a string starting with "Error:"
            results = run_query(sql_query)
            
            # 3. Check for DB Errors
            if isinstance(results, str) and results.startswith("Error"):
                raise Exception(results) # Force retry logic
            
            # If successful, return the dict
            return results
            
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ SQL Failed: {error_msg}")
            
            # --- FIX: Wait before retrying ---
            print("💤 Waiting 2s before retry...")
            time.sleep(2)  # <--- NEW LINE
            
            if sql_query == "UNKNOWN_SQL":
                attempt += 1
                continue 

            current_prompt = ERROR_PROMPT.format(
                question=question,
                sql=sql_query,
                error=error_msg
            )
            attempt += 1
    
    return "❌ Failed to generate valid SQL after 3 attempts."

# --- TEST AREA ---
if __name__ == "__main__":
    answer = ask_data("Show me the top 3 Customer names who spent the most money.")
    print(answer)