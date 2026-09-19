import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & ENTERPRISE UI STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="E&E Opti Lab Executive Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #0f172a; }
    
    /* Executive Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .metric-title { color: #64748b; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { color: #0f172a; font-size: 26px; font-weight: 900; margin-top: 4px; }

    /* Kanban Card Container */
    .kanban-card {
        background-color: #ffffff;
        border-left: 4px solid #2563eb;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        padding: 14px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
    }
    
    .stButton>button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION ENGINE (PURE SQL BACKEND)
# -----------------------------------------------------------------------------
def get_connection():
    return sqlite3.connect('opti_lab_master.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Master Tasks Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_tasks (
            task_id TEXT PRIMARY KEY,
            parent_id TEXT,
            lab_name TEXT,
            bin_pack_number TEXT,
            dvp_name TEXT,
            category TEXT,
            trf_id TEXT,
            priority TEXT,
            sprint_id TEXT,
            lead_engineer TEXT,
            shift_incharge TEXT,
            assigned_associate TEXT,
            target_shift TEXT,
            target_units INTEGER,
            completed_units INTEGER,
            progress_percent TEXT,
            status TEXT,
            start_date TEXT,
            target_end_date TEXT,
            data_link TEXT,
            observations TEXT
        )
    ''')
    
    # Attendance Ledger
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operator TEXT,
            shift TEXT,
            lab TEXT,
            punch_type TEXT
        )
    ''')

    # Audit History Feed
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            lab TEXT,
            shift TEXT,
            task_id TEXT,
            operator TEXT,
            action TEXT,
            notes TEXT
        )
    ''')

    # Seed Initial Data if Empty
    c.execute("SELECT COUNT(*) FROM master_tasks")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO master_tasks VALUES 
            ('TSK-599727', '', 'BatteryLab_Tasks', '450-9702', 'TL-9 Profile', '450', 'EL-46497', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Unassigned', 'Shift A', 1000, 314, '31%', 'Running', '2026-09-01', '2026-09-10', '', '[Objective]: Evaluate battery pack performance under high temperature cycling'),
            ('SUB-839376', 'TSK-599727', 'BatteryLab_Tasks', '450-9702', '3. Life Cycle', '450', 'EL-46497', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Sathya', 'Shift A', 1000, 398, '40%', 'Running', '2026-09-01', '2026-09-10', '', 'Chamber operating at 45C'),
            ('SUB-766448', 'TSK-599727', 'BatteryLab_Tasks', '450-9702', '4. Post Capacity', '450', 'EL-46497', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Sanjay', 'Shift A', 1, 0, '0%', 'To Do', '2026-09-01', '2026-09-10', '', ''),
            ('TSK-918058', '', 'BatteryLab_Tasks', 'BFGMBC14000136', 'TL-2 Thermal', '450', 'EL-88391', 'P2', '27.2.1', 'Yeshwanth', 'Raja', 'Unassigned', 'Shift B', 1553, 1510, '97%', 'Running', '2026-09-02', '2026-09-12', '', '[Objective]: Thermal stress validation run'),
            ('SUB-954598', 'TSK-918058', 'BatteryLab_Tasks', 'BFGMBC14000136', '3. Thermal Cycling', '450', 'EL-88391', 'P2', '27.2.1', 'Yeshwanth', 'Raja', 'Yosvaraj', 'Shift B', 1553, 1510, '97%', 'Awaiting Resource', '2026-09-02', '2026-09-12', '', 'Chamber sensor issue flagged'),
            ('TSK-400101', '', 'CellLab_Tasks', 'CELL-NMC-881', 'Cell Formation Flow', 'NMC Cylindrical', 'EL-99011', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Unassigned', 'Shift A', 100, 50, '50%', 'Running', '2026-09-05', '2026-09-15', '', '[Objective]: Cell formation and wetting protocol'),
            ('TSK-700202', '', 'Vibration_Tasks', 'VIB-AM-002', 'Vibration Standard Flow', 'Structural', 'EL-33410', 'P1', '27.2.1', 'Yeshwanth', 'Riyaz', 'Unassigned', 'Shift A', 24, 8, '33%', 'Running', '2026-09-05', '2026-09-15', '', '[Objective]: Component vibration stress testing')
        """)
        conn.commit()

    conn.close()

init_db()

# -----------------------------------------------------------------------------
# LAB DEPARTMENT CONFIGURATIONS
# -----------------------------------------------------------------------------
LAB_CONFIG = {
    "🔋 Battery Lab": {
        "key": "BatteryLab_Tasks",
        "shiftIncharges": ["Praveen kumar", "Raja", "Riyaz"],
        "associates": ["Sathya", "Sanjay", "Yosvaraj", "Lal krishna", "Bharani"],
        "categories": ["450", "Diesel", "EL"],
        "blueprints": {
            "TL-1 Profile": ["1. Pre-Test Check", "2. Pre-Capacity", "3. Random Vibration", "4. Post Capacity", "5. Air Leak Test"],
            "TL-2 Thermal": ["1. Pre-Test Check", "2. Thermal Cycling", "3. Post Capacity", "4. Air Leak Test"],
            "TL-9 Life Cycle": ["1. Pre-Test Check", "2. Life Cycle (1000 Cycles)", "3. Post Capacity", "4. Air Leak Test"]
        }
    },
    "🧪 Cell Lab": {
        "key": "CellLab_Tasks",
        "shiftIncharges": ["Praveen kumar", "Raja"],
        "associates": ["Sathya", "Sanjay", "Yosvaraj"],
        "categories": ["NMC Cylindrical", "LFP Prismatic", "Solid State Pouch"],
        "blueprints": {
            "Cell Formation": ["1. Electrolyte Wetting", "2. Initial C-Rate Formation", "3. Degassing Stamping"]
        }
    },
    "⚡ Vibration Team": {
        "key": "Vibration_Tasks",
        "shiftIncharges": ["Riyaz", "Raja"],
        "associates": ["Gowtham P", "Karthick G Prabhu", "Sanjay Mathad", "Midhun S", "Devakar V", "Yuvaraji R"],
        "categories": ["Battery", "E&E compo", "Structural", "AM/CI"],
        "blueprints": {
            "Vibration Standard Flow": ["1. Pre-Test Photos", "2. DUT Mounting", "3. X-Axis Run", "4. Y-Axis Run", "5. Z-Axis Run", "6. Post Test Photos"]
        }
    },
    "⚡ E&E Lab": {
        "key": "EELab_Tasks",
        "shiftIncharges": ["Praveen kumar", "Riyaz"],
        "associates": ["Sathya", "Sanjay", "Lal krishna"],
        "categories": ["BMS Controller", "MCU Inverter", "VCU Harness Bench"],
        "blueprints": {
            "CAN Validation": ["1. Baud Validation", "2. Frame Stress Run", "3. Diagnostic Verification"]
        }
    }
}

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & LAB SELECTOR
# -----------------------------------------------------------------------------
st.sidebar.markdown("<h2 style='color:#2563eb; margin-bottom:0;'>⚡ E&E OPTI LAB</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#64748b; font-size:11px; font-weight:800; text-transform:uppercase;'>EXECUTIVE CONSOLE</p>", unsafe_allow_html=True)

# 1. LAB SELECTION DROPDOWN (ALL 4 LABS AVAILABLE)
selected_lab_label = st.sidebar.selectbox(
    "🏢 SELECT DEPARTMENT LAB", 
    list(LAB_CONFIG.keys())
)

lab_info = LAB_CONFIG[selected_lab_label]
active_lab_key = lab_info["key"]

st.sidebar.divider()

# 2. MODULE CONSOLE SELECTION
active_module = st.sidebar.radio("Navigation Console", [
    "📊 Dashboard 1 (Engineering)", 
    "📋 Task Planner", 
    "☀️ Shift Workbench", 
    "📈 Dashboard 2 (Analytics)", 
    "📑 TRF Gateway"
])

# Helper Function to Fetch Data for Active Lab
def load_active_lab_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM master_tasks WHERE lab_name = ?", conn, params=(active_lab_key,))
    conn.close()
    return df

df_all = load_active_lab_data()

# -----------------------------------------------------------------------------
# MODULE 1: DASHBOARD 1 (ENGINEERING COMMAND CENTER)
# -----------------------------------------------------------------------------
if active_module == "📊 Dashboard 1 (Engineering)":
    st.title(f"📊 Dashboard 1 — {selected_lab_label.upper()}")
    
    master_tasks = df_all[(df_all['parent_id'] == '') | (df_all['parent_id'].isna())]
    
    # Key Metric Cards Deck
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Master DVP Tasks</div>
            <div class="metric-value">{len(master_tasks)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        running_cnt = len(master_tasks[master_tasks['status'] == 'Running'])
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #16a34a;">
            <div class="metric-title">Running Runs 🟢</div>
            <div class="metric-value">{running_cnt}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        complete_cnt = len(master_tasks[master_tasks['status'].isin(['Complete', 'Closed & Certified'])])
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #2563eb;">
            <div class="metric-title">Completed ✅</div>
            <div class="metric-value">{complete_cnt}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        blocked_cnt = len(master_tasks[master_tasks['status'] == 'Awaiting Resource'])
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #dc2626;">
            <div class="metric-title">Awaiting Resource 🛑</div>
            <div class="metric-value">{blocked_cnt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Search & Filter Engine
    st.subheader("🔍 Search & Filter Matrix")
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    search_q = f_col1.text_input("Fuzzy Search TRF ID, BIN Number, or DVP Name")
    sprint_f = f_col2.selectbox("Sprint Allocation", ["ALL", "27.2.1", "27.1.2"])
    status_f = f_col3.selectbox("Status", ["ALL", "Running", "To Do", "Complete", "Awaiting Resource"])

    filtered_df = master_tasks.copy()
    if search_q:
        filtered_df = filtered_df[
            filtered_df['task_id'].str.contains(search_q, case=False) |
            filtered_df['bin_pack_number'].str.contains(search_q, case=False) |
            filtered_df['trf_id'].str.contains(search_q, case=False) |
            filtered_df['dvp_name'].str.contains(search_q, case=False)
        ]
    if sprint_f != "ALL":
        filtered_df = filtered_df[filtered_df['sprint_id'] == sprint_f]
    if status_f != "ALL":
        filtered_df = filtered_df[filtered_df['status'] == status_f]

    st.dataframe(
        filtered_df[['task_id', 'priority', 'bin_pack_number', 'trf_id', 'dvp_name', 'lead_engineer', 'progress_percent', 'sprint_id', 'status', 'observations']],
        use_container_width=True
    )

# -----------------------------------------------------------------------------
# MODULE 2: TASK PLANNER (BLUEPRINT GENERATOR)
# -----------------------------------------------------------------------------
elif active_module == "📋 Task Planner":
    st.title(f"📋 Task Planner & Blueprint Generator — {selected_lab_label}")
    
    st.subheader("Active Pending Shift Workload Matrix")
    p_col1, p_col2, p_col3 = st.columns(3)
    subs_all = df_all[df_all['parent_id'] != '']
    
    load_a = len(subs_all[(subs_all['target_shift'] == 'Shift A') & (~subs_all['status'].isin(['Complete', 'Closed & Certified']))])
    load_b = len(subs_all[(subs_all['target_shift'] == 'Shift B') & (~subs_all['status'].isin(['Complete', 'Closed & Certified']))])
    load_c = len(subs_all[(subs_all['target_shift'] == 'Shift C') & (~subs_all['status'].isin(['Complete', 'Closed & Certified']))])

    p_col1.info(f"**Shift A Queue:** {load_a} Tasks")
    p_col2.info(f"**Shift B Queue:** {load_b} Tasks")
    p_col3.info(f"**Shift C Queue:** {load_c} Tasks")

    st.markdown("---")

    st.subheader("➕ Create New Master DVP Task & Subtask Sequence")
    with st.form("task_creation_form"):
        c1, c2, c3 = st.columns(3)
        bin_no = c1.text_input("BIN / Pack Barcode *", placeholder="e.g. BGFT5B17000619")
        dvp_name = c2.text_input("DVP Profile Name *", placeholder="e.g. STB Pack Profile")
        priority_val = c3.selectbox("Priority *", ["P1", "P2", "P3", "P4"])

        c4, c5 = st.columns(2)
        pack_cat = c4.selectbox("Category Classification", lab_info["categories"])
        trf_id_val = c5.text_input("TRF Reference ID", placeholder="e.g. EL-46497")

        blueprint_code = st.selectbox("Select Profile Blueprint", ["CUSTOM"] + list(lab_info["blueprints"].keys()))
        obj_text = st.text_area("Test Objective & Background *", placeholder="e.g. Evaluate battery pack performance under high temperature cycling")

        c6, c7, c8 = st.columns(3)
        lead_eng_val = c6.text_input("Lead Engineer", "Yeshwanth")
        target_shift_val = c7.selectbox("Target Initial Shift", ["Shift A", "Shift B", "Shift C"])
        sprint_val = c8.selectbox("Target Sprint Allocation", ["27.2.1", "27.1.2"])

        manager_pin = st.password_input("Manager Security PIN * (1234)")

        submitted = st.form_submit_button("💾 GENERATE TASK BLUEPRINT")

        if submitted:
            if not bin_no or not dvp_name or not obj_text:
                st.error("Please fill in all mandatory fields (BIN Barcode, DVP Name, and Test Objective).")
            elif manager_pin != "1234":
                st.error("Invalid Manager Security PIN.")
            else:
                conn = get_connection()
                c = conn.cursor()
                
                master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
                today_str = datetime.now().strftime('%Y-%m-%d')
                
                c.execute("""
                    INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    master_id, "", active_lab_key, bin_no, dvp_name, pack_cat, trf_id_val, priority_val, sprint_val,
                    lead_eng_val, "Praveen kumar", "Unassigned", target_shift_val, 100, 0, "0%",
                    "Running", today_str, today_str, "", f"[Objective]: {obj_text}"
                ))

                # Append Blueprint Steps if selected
                if blueprint_code in lab_info["blueprints"]:
                    steps = lab_info["blueprints"][blueprint_code]
                    for idx, step_name in enumerate(steps):
                        sub_id = f"SUB-{master_id.replace('TSK-','')}-{idx+1}"
                        c.execute("""
                            INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sub_id, master_id, active_lab_key, bin_no, step_name, pack_cat, trf_id_val, priority_val, sprint_val,
                            lead_eng_val, "Praveen kumar", "Unassigned", target_shift_val, 100 if "Cycle" in step_name else 1, 0, "0%",
                            "To Do", today_str, today_str, "", ""
                        ))

                conn.commit()
                conn.close()
                st.success(f"✅ Master Task [{master_id}] & Child Steps Created Successfully for {selected_lab_label}!")
                st.rerun()

# -----------------------------------------------------------------------------
# MODULE 3: SHIFT EXECUTION WORKBENCH (KANBAN)
# -----------------------------------------------------------------------------
elif active_module == "☀️ Shift Workbench":
    st.title(f"☀️ Shift Execution Workbench — {selected_lab_label.upper()}")

    # Floor Associate Check-In Desk
    with st.expander("👤 Floor Associate Attendance Check-In Desk", expanded=True):
        ac1, ac2, ac3 = st.columns([2, 1, 1])
        operator_sel = ac1.selectbox("Select Associate / Technician", lab_info["shiftIncharges"] + lab_info["associates"])
        
        if ac2.button("⏰ START SHIFT (CHECK IN)"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO attendance_ledger (timestamp, operator, shift, lab, punch_type) VALUES (?, ?, ?, ?, ?)",
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), operator_sel, "Shift A", active_lab_key, "CHECK_IN"))
            conn.commit()
            conn.close()
            st.success(f"Check-In Logged for {operator_sel}")

        if ac3.button("🚪 END SHIFT (CHECK OUT)"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO attendance_ledger (timestamp, operator, shift, lab, punch_type) VALUES (?, ?, ?, ?, ?)",
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), operator_sel, "Shift A", active_lab_key, "CHECK_OUT"))
            conn.commit()
            conn.close()
            st.warning(f"Check-Out Logged for {operator_sel}")

    active_shift = st.radio("Select Active Floor Execution Shift", ["Shift A", "Shift B", "Shift C"], horizontal=True)

    # Filter Active Subtasks
    subtasks_shift = df_all[(df_all['parent_id'] != '') & (df_all['target_shift'] == active_shift) & (~df_all['status'].isin(['Complete', 'Closed & Certified']))]

    col_todo, col_run, col_block = st.columns(3)

    with col_todo:
        st.subheader("📋 TO DO (ASSIGNED)")
        todo_df = subtasks_shift[subtasks_shift['status'] == 'To Do']
        for _, row in todo_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="kanban-card">
                    <div style="font-size:10px; font-weight:800; color:#2563eb;">{row['task_id']}</div>
                    <div style="font-size:13px; font-weight:700; color:#0f172a;">{row['dvp_name']}</div>
                    <div style="font-size:11px; color:#64748b; margin-top:4px;">Pack Barcode: {row['bin_pack_number']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                new_assoc = st.selectbox("Assign Operator", ["Unassigned"] + lab_info["associates"], key=f"sel_{row['task_id']}")
                if st.button("Save Associate 💾", key=f"btn_{row['task_id']}"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE master_tasks SET assigned_associate = ?, status = 'Running' WHERE task_id = ?", (new_assoc, row['task_id']))
                    conn.commit()
                    conn.close()
                    st.success("Updated!")
                    st.rerun()

    with col_run:
        st.subheader("🟢 IN PROGRESS / RUNNING")
        run_df = subtasks_shift[subtasks_shift['status'] == 'Running']
        for _, row in run_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="kanban-card" style="border-left: 4px solid #16a34a;">
                    <div style="font-size:10px; font-weight:800; color:#16a34a;">{row['task_id']}</div>
                    <div style="font-size:13px; font-weight:700; color:#0f172a;">{row['dvp_name']}</div>
                    <div style="font-size:11px; color:#64748b;">Assigned: <b>{row['assigned_associate']}</b></div>
                    <div style="font-size:11px; color:#64748b;">Completed: {row['completed_units']} / {row['target_units']} Units</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.popover("Update Progress ➔"):
                    new_units = st.number_input("Actual Completed Units", min_value=0, value=int(row['completed_units']), key=f"u_{row['task_id']}")
                    new_st = st.selectbox("Status", ["Running", "Complete", "Awaiting Resource"], key=f"st_{row['task_id']}")
                    shift_notes = st.text_area("Handover Observation Notes", key=f"n_{row['task_id']}")
                    
                    if st.button("Submit Progress ➔", key=f"sav_{row['task_id']}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, observations = ? WHERE task_id = ?",
                                  (new_units, new_st, shift_notes, row['task_id']))
                        conn.commit()
                        conn.close()
                        st.success("Progress Saved!")
                        st.rerun()

    with col_block:
        st.subheader("🛑 BLOCKED / 3M ISSUES")
        block_df = subtasks_shift[subtasks_shift['status'] == 'Awaiting Resource']
        for _, row in block_df.iterrows():
            st.error(f"**{row['task_id']} — {row['dvp_name']}**\n\nNotes: {row['observations']}")

# -----------------------------------------------------------------------------
# MODULE 4: DASHBOARD 2 (ANALYTICS & AUDIT STREAM)
# -----------------------------------------------------------------------------
elif active_module == "📈 Dashboard 2 (Analytics)":
    st.title(f"📈 Dashboard 2 — {selected_lab_label} Analytics")
    
    st.subheader("📅 Associate Monthly Attendance Summary")
    conn = get_connection()
    df_att = pd.read_sql_query("SELECT * FROM attendance_ledger WHERE lab = ?", conn, params=(active_lab_key,))
    conn.close()

    if not df_att.empty:
        st.dataframe(df_att, use_container_width=True)
    else:
        st.info(f"No punch records logged for {selected_lab_label} yet.")

    st.markdown("---")
    
    st.subheader("🏆 Associate Task Output Scorecard")
    done_subs = df_all[(df_all['parent_id'] != '') & (df_all['status'].isin(['Complete', 'Closed & Certified']))]
    if not done_subs.empty:
        scorecard = done_subs['assigned_associate'].value_counts().reset_index()
        scorecard.columns = ['Associate Name', 'Completed Tasks']
        st.dataframe(scorecard, use_container_width=True)
    else:
        st.caption("No completed subtask steps logged yet.")

# -----------------------------------------------------------------------------
# MODULE 5: STANDALONE TRF GATEWAY
# -----------------------------------------------------------------------------
elif active_module == "📑 TRF Gateway":
    st.title(f"📑 Standalone TRF Certification & Report Desk — {selected_lab_label}")
    
    master_tasks = df_all[(df_all['parent_id'] == '') | (df_all['parent_id'].isna())]
    
    st.dataframe(
        master_tasks[['task_id', 'bin_pack_number', 'trf_id', 'dvp_name', 'lead_engineer', 'progress_percent', 'status', 'data_link']],
        use_container_width=True
    )
