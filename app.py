# --- 1. CRITICAL FIX: MUST BE AT THE VERY TOP ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import os
import sqlite3
import google.generativeai as genai

# --- PAGE SETUP ---
st.set_page_config(page_title="InsightIQ Debugger", page_icon="🔧")
st.title("🔧 InsightIQ Diagnostics")

# --- CHECK 1: SQLITE VERSION (For ChromaDB) ---
st.header("1. System Check")
sqlite_version = sqlite3.sqlite_version
st.write(f"**SQLite Version:** `{sqlite_version}`")

if sqlite_version < "3.35.0":
    st.error("❌ SQLite version is too old! ChromaDB will crash.")
else:
    st.success("✅ SQLite version is good (>= 3.35.0).")

# --- CHECK 2: DATABASE FILE ---
st.header("2. Database Check")
if os.path.exists("chinook.db"):
    st.success(f"✅ 'chinook.db' found! Size: {os.path.getsize('chinook.db')/1024:.2f} KB")
else:
    st.error("❌ 'chinook.db' NOT FOUND. The app cannot query data.")
    st.info("💡 Fix: Run `git add -f chinook.db`, commit, and push again.")

# --- CHECK 3: API KEY ---
st.header("3. API Key Check")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Try getting it from st.secrets as a backup
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        os.environ["GEMINI_API_KEY"] = api_key # Inject back to env for other scripts
        st.success("✅ API Key found in `st.secrets`.")
    except:
        st.error("❌ API Key is MISSING.")
        st.info("💡 Fix: Go to 'Manage App' -> 'Settings' -> 'Secrets' and add GEMINI_API_KEY.")
else:
    st.success("✅ API Key found in Environment Variables.")

# --- CHECK 4: GEMINI CONNECTIVITY ---
st.header("4. AI Connectivity Test")
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        with st.spinner("🤖 Testing Gemini API connection..."):
            response = model.generate_content("Say 'Hello' if you can hear me.")
            st.success(f"✅ Gemini Responded: {response.text}")
    except Exception as e:
        st.error(f"❌ Gemini Connection Failed: {e}")

# --- RESTORE APP BUTTON ---
st.divider()
st.subheader("🏁 Ready to run the real app?")
if st.button("Run Main App"):
    # This imports the real app logic ONLY if everything above passes
    from src.llm_engine import ask_data
    import pandas as pd
    
    st.markdown("---")
    st.subheader("📊 InsightIQ Chat")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "data" in message:
                st.dataframe(message["data"])

    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                response = ask_data(prompt)
                
                if isinstance(response, str):
                    st.error(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    columns = response["columns"]
                    data = response["data"]
                    df = pd.DataFrame(data, columns=columns)
                    st.success("✅ Data Retrieved")
                    st.dataframe(df)
                    st.session_state.messages.append({"role": "assistant", "content": "Results:", "data": df})