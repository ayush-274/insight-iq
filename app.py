# --- CHROMA DB FIX FOR STREAMLIT CLOUD ---
try:
    # This specifically fixes the "Old SQLite" error on Cloud servers
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    # If we are on your laptop (which works fine), pass over this
    pass
import streamlit as st
import pandas as pd
from src.llm_engine import ask_data

st.set_page_config(page_title="InsightIQ", page_icon="📊")

st.title("📊 InsightIQ: AI Data Analyst")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "data" in message:
            st.dataframe(message["data"])

if prompt := st.chat_input("Ex: Total sales by Country"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            response = ask_data(prompt)
            
            # 1. Handle Errors
            if isinstance(response, str):
                st.error(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # 2. Extract Data & Columns
                columns = response["columns"]
                data = response["data"]
                
                # 3. Create DataFrame
                df = pd.DataFrame(data, columns=columns)
                
                st.success("✅ Here is the data:")
                st.dataframe(df)
                
                # 4. Auto-Visualization Logic
                # Only graph if we have exactly 2 columns (e.g., Label vs Value)
                # 4. Auto-Visualization Logic
                if len(df.columns) == 2:
                    x_col = df.columns[0]  # Label (e.g., "Country")
                    y_col = df.columns[1]  # Value (e.g., "Total Sales")
                    
                    st.write(f"📊 **Analysis: {x_col} vs {y_col}**")
                    
                    # --- FIX: Clean the Data ---
                    try:
                        # 1. Force Y-axis to numeric (coerce errors to NaN)
                        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                        
                        # 2. Drop any rows that failed conversion (NaNs)
                        df = df.dropna(subset=[y_col])
                        
                        # 3. Explicitly tell Streamlit what is X and Y
                        # (This is safer than set_index)
                        st.bar_chart(
                            data=df,
                            x=x_col,
                            y=y_col,
                            color="#4A90E2" # Optional: Makes it look professional
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Could not generate graph: {e}")
                        # Debugging: Show raw data types if it fails
                        st.write("Debug Data Types:", df.dtypes)

                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "✅ Results:",
                    "data": df
                })