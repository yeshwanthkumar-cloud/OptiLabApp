import streamlit as st
import sqlite3
import pandas as pd
from database import init_db

# Initialize Database on Startup
init_db()

st.set_page_config(page_title="E&E Opti Lab Console", page_icon="⚡", layout="wide")

def get_connection():
    return sqlite3.connect('optilab.db')

st.title("⚡ E&E Opti Lab Console (Pure Python + SQL)")

# Sidebar Navigation
module = st.sidebar.radio("Navigation Console", ["📊 Dashboard", "📋 Task Planner", "☀️ Shift Workbench"])

# -----------------------------------------------------------------------------
# MODULE 1: DASHBOARD
# -----------------------------------------------------------------------------
if module == "📊 Dashboard":
    st.header("📊 Master DVP Tasks Overview")
    conn = get_connection()
    df_master = pd.read_sql_query("SELECT * FROM master_tasks", conn)
    conn.close()
    
    if not df_master.empty:
        st.dataframe(df_master, use_container_width=True)
    else:
        st.info("No master tasks created yet. Go to Task Planner to add tasks.")

# -----------------------------------------------------------------------------
# MODULE 2: TASK PLANNER
# -----------------------------------------------------------------------------
elif module == "📋 Task Planner":
    st.header("📋 Create New DVP Task")
    with st.form("create_task"):
        bin_pack = st.text_input("BIN / Pack Barcode (e.g. BGFT5B17000619)")
        dvp_name = st.text_input("DVP Profile Name (e.g. STB Pack Profile)")
        priority = st.selectbox("Priority", ["P1", "P2", "P3", "P4"])
        sprint = st.selectbox("Sprint Allocation", ["27.2.1", "27.2.2"])
        lead_eng = st.text_input("Lead Engineer", "Yeshwanth")
        
        submitted = st.form_submit_button("Save Blueprint to Database 💾")
        if submitted and bin_pack and dvp_name:
            conn = get_connection()
            c = conn.cursor()
            task_id = f"TSK-{pd.Timestamp.now().strftime('%H%M%S')}"
            
            c.execute("""
                INSERT INTO master_tasks (task_id, bin_pack, dvp_name, priority, sprint_id, lead_engineer, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, bin_pack, dvp_name, priority, sprint, lead_eng, "Running"))
            
            conn.commit()
            conn.close()
            st.success(f"Task {task_id} created successfully!")

# -----------------------------------------------------------------------------
# MODULE 3: SHIFT WORKBENCH (KANBAN)
# -----------------------------------------------------------------------------
elif module == "☀️ Shift Workbench":
    st.header("☀️ Shift Execution Workbench")
    active_shift = st.selectbox("Select Active Shift", ["Shift A", "Shift B", "Shift C"])
    
    conn = get_connection()
    df_subs = pd.read_sql_query("SELECT * FROM subtasks WHERE target_shift = ?", conn, params=(active_shift,))
    conn.close()
    
    c1, c2, c3 = st.columns(3)
    c1.subheader("📋 To Do")
    c2.subheader("🟢 Running")
    c3.subheader("🛑 Blocked")