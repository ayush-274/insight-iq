# InsightIQ: Autonomous Text-to-SQL Agent

**Live Demo:** [[Link to the Streamlit App]](https://insight-iq-ayush.streamlit.app/)

## Overview
InsightIQ is an AI-powered Business Intelligence agent that democratizes data access. It allows non-technical users to query complex SQL databases using natural language. Unlike standard chatbots, it uses **RAG** for schema scalability and an **Agentic Self-Correction Loop** to ensure query accuracy.

## Tech Stack
* **AI Engine:** Google Gemini 1.5 Flash
* **Orchestration:** Python (Custom Agent Logic)
* **Database:** SQLite (Chinook Dataset)
* **Vector Store:** ChromaDB (Schema Indexing)
* **Frontend:** Streamlit Cloud

## Key Features
* **RAG Architecture:** Dynamically retrieves only relevant table schemas to handle large databases.
* **Self-Healing SQL:** Automatically detects database errors and retries with corrected logic.
* **Auto-Visualization:** Intelligently plots Bar/Line charts based on data types.
* **Secure:** Read-only permissions to prevent data loss.

## How to Run Locally
1. Clone the repo
2. `pip install -r requirements.txt`
3. Setup `.env` with `GEMINI_API_KEY`
4. `streamlit run app.py`
