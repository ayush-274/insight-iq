# --- 1. CRITICAL: SQLITE FIX FOR CLOUD (Must be at the very top) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import pandas as pd
import os
from src.llm_engine import ask_data

# --- 2. SETUP PAGE ---
st.set_page_config(page_title="InsightIQ", page_icon="📊")
st.title("📊 InsightIQ: AI Data Analyst")

# --- 3. CLOUD SECRETS BRIDGE ---
# This ensures the API key from Streamlit Secrets works with your other scripts
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# --- 4. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "data" in message:
            st.dataframe(message["data"])

# --- 5. MAIN LOGIC ---
if prompt := st.chat_input("Ask a question (e.g., 'Top 5 invoices')"):
    # Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show AI Response
    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            
            # CALL THE BRAIN
            response = ask_data(prompt)
            
            # HANDLE ERRORS
            if isinstance(response, str):
                st.error(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # HANDLE SUCCESS
            else:
                columns = response["columns"]
                data = response["data"]
                
                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)
                
                st.success("✅ Analysis Complete")
                st.dataframe(df)
                
                # AUTO-VISUALIZATION (Bar Chart)
                if len(df.columns) == 2:
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    st.write(f"📊 **Visualizing: {x_col} vs {y_col}**")
                    
                    try:
                        # Clean data for plotting
                        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                        df = df.dropna(subset=[y_col])
                        
                        st.bar_chart(data=df, x=x_col, y=y_col, color="#4A90E2")
                    except Exception as e:
                        st.warning(f"Could not graph: {e}")

                # Save to History
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "✅ Analysis Complete",
                    "data": df
                })