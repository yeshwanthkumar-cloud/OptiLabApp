import sqlite3

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
            bin_pack TEXT,
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
            observations TEXT
        )
    ''')
    
    # Audit History & Reasons Log
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            lab_name TEXT,
            shift TEXT,
            task_id TEXT,
            operator TEXT,
            action TEXT,
            notes TEXT
        )
    ''')

    # Seed Sample Data
    c.execute("SELECT COUNT(*) FROM master_tasks")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO master_tasks VALUES 
            ('TSK-599727', '', 'BatteryLab_Tasks', '450-9702', 'TL-9 Life Cycle', '450', 'EL-46497', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Unassigned', 'Shift A', 1000, 314, '31%', 'Running', '[Objective]: Thermal stress validation run'),
            ('SUB-839376', 'TSK-599727', 'BatteryLab_Tasks', '450-9702', '3. Life Cycle Run', '450', 'EL-46497', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Sathya', 'Shift A', 1000, 398, '40%', 'Running', 'Chamber operating at 45C'),
            ('SUB-766448', 'TSK-599727', 'BatteryLab_Tasks', '450-9702', '4. Post Capacity Test', '450', 'EL-46497', 'P1', '27.2.1', 'Yeshwanth', 'Praveen kumar', 'Sanjay', 'Shift A', 1, 0, '0%', 'To Do', ''),
            ('TSK-918058', '', 'BatteryLab_Tasks', 'BFGMBC14000136', 'TL-2 Thermal Run', '450', 'EL-88391', 'P2', '27.2.1', 'Yeshwanth', 'Raja', 'Unassigned', 'Shift B', 1500, 1200, '80%', 'Running', '[Objective]: High temperature validation'),
            ('SUB-954598', 'TSK-918058', 'BatteryLab_Tasks', 'BFGMBC14000136', '3. Thermal Cycling', '450', 'EL-88391', 'P2', '27.2.1', 'Yeshwanth', 'Raja', 'Yosvaraj', 'Shift B', 1500, 1200, '80%', 'Awaiting Resource', 'Chamber sensor tripped during cycle 120')
        """)
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully!")
