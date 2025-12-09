import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.database import get_schema, run_query

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
    
    # Setup Schema
    schema_dict = get_schema()
    schema_str = "\n".join([f"Table {table}: {cols}" for table, cols in schema_dict.items()])
    
    # Initial Prompt
    current_prompt = BASE_PROMPT.format(schema=schema_str) + f"\nUser Question: {question}"
    
    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        print(f"⏳ Thinking... (Attempt {attempt+1}/{max_retries})")
        
        try:
            # 1. Ask Gemini
            response = model.generate_content(current_prompt)
            sql_query = clean_sql(response.text)
            
            if "ERROR" in sql_query:
                return "❌ AI could not understand the question."

            print(f"📝 Generated SQL: {sql_query}")
            
            # 2. Run SQL (This function catches DB errors and returns them as strings)
            results = run_query(sql_query)
            
            # 3. Check if 'results' is actually an error message string
            # (Our database.py returns a string starting with "Error:" if it fails)
            if isinstance(results, str) and results.startswith("Error"):
                raise Exception(results) # Force it to go to the 'except' block
            
            # If we get here, it worked!
            return results
            
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ SQL Failed: {error_msg}")
            
            # 4. PREPARE THE SELF-CORRECTION
            # We feed the error back into the prompt for the next loop
            current_prompt = ERROR_PROMPT.format(
                question=question,
                sql=sql_query,
                error=error_msg
            )
            attempt += 1
    
    return "❌ Failed to generate valid SQL after 3 attempts."

# --- TEST AREA ---
if __name__ == "__main__":
    # Test 1: The Easy One
    print("--- Test 1 (Easy) ---")
    ask_data("Top 3 customers")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: The Trick Question (To trigger Self-Correction)
    # The database has 'FirstName', but we will ask for 'First_Name' (underscore)
    # A naive AI might hallucinate 'First_Name', causing an error.
    # The Agent should catch it, realize 'First_Name' doesn't exist, and switch to 'FirstName'.
    print("--- Test 2 (Self-Correction) ---")
    results = ask_data("Show me the full name (combined first and last) of all employees.")
    
    print("\n📊 Final Results:")
    if isinstance(results, list):
        for row in results[:3]: # Print just first 3
            print(row)
    else:
        print(results)