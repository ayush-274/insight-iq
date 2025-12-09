import sqlite3
import requests
import os

# URL to the raw SQL script for Chinook DB
DB_URL = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
DB_FILE = "chinook.db"

def init_db():
    if os.path.exists(DB_FILE):
        print(f"✅ {DB_FILE} already exists. Skipping download.")
        return

    print("⏳ Downloading Chinook Database SQL script...")
    response = requests.get(DB_URL)
    sql_script = response.text

    print("⏳ Creating Database and inserting data...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Execute the SQL script
    cursor.executescript(sql_script)
    
    conn.commit()
    conn.close()
    print(f"🚀 Success! Database created at '{DB_FILE}'")

if __name__ == "__main__":
    init_db()