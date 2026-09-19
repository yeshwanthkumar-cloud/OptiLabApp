import sqlite3

def get_connection():
    return sqlite3.connect('opti_lab_master.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Master Tasks Table (Supports Priority P1-P3, BINs, Sprints, Subtasks)
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
            assign_date TEXT,
            target_units INTEGER,
            completed_units INTEGER,
            unit_type TEXT,
            equipment_id TEXT,
            progress_percent TEXT,
            status TEXT,
            background TEXT,
            observations TEXT,
            target_end_date TEXT
        )
    ''')

    # Custom Dynamic Test Flows (Top-Right Task Flow Creator)
    c.execute('''
        CREATE TABLE IF NOT EXISTS custom_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            flow_name TEXT,
            step_order INTEGER,
            step_name TEXT
        )
    ''')

    # Registered Associates per Lab
    c.execute('''
        CREATE TABLE IF NOT EXISTS associates_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            associate_name TEXT
        )
    ''')

    # Tested Component Categories
    c.execute('''
        CREATE TABLE IF NOT EXISTS components_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            component_name TEXT
        )
    ''')

    # Monthly Shift Roster
    c.execute('''
        CREATE TABLE IF NOT EXISTS shift_roster (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            operator_name TEXT,
            assigned_shift TEXT,
            effective_month TEXT
        )
    ''')

    # Attendance & 5S Handover Ledger
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operator TEXT,
            shift TEXT,
            lab_name TEXT,
            punch_type TEXT,
            s5_verified INTEGER
        )
    ''')

    # Audit History & Shift Notes Log
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

    # Seed Default Associates
    c.execute("SELECT COUNT(*) FROM associates_master")
    if c.fetchone()[0] == 0:
        assoc_seeds = [
            ('BatteryLab_Tasks', 'Sathya'),
            ('BatteryLab_Tasks', 'Sanjay'),
            ('BatteryLab_Tasks', 'Yosvaraj'),
            ('BatteryLab_Tasks', 'Bharani'),
            ('CellLab_Tasks', 'Arun'),
            ('CellLab_Tasks', 'Karthik'),
            ('Vibration_Tasks', 'Vignesh'),
            ('EELab_Tasks', 'Deepak')
        ]
        c.executemany("INSERT INTO associates_master (lab_name, associate_name) VALUES (?, ?)", assoc_seeds)

    # Seed Default Tested Components
    c.execute("SELECT COUNT(*) FROM components_master")
    if c.fetchone()[0] == 0:
        comp_seeds = [
            ('BatteryLab_Tasks', '450 Pack'),
            ('BatteryLab_Tasks', 'DIESEL Pack'),
            ('BatteryLab_Tasks', 'EL Pack'),
            ('CellLab_Tasks', 'NMC Cell'),
            ('CellLab_Tasks', 'LFP Cell'),
            ('Vibration_Tasks', 'Mounting Bracket'),
            ('EELab_Tasks', 'BMS Board')
        ]
        c.executemany("INSERT INTO components_master (lab_name, component_name) VALUES (?, ?)", comp_seeds)

    # Seed Default Flow Blueprints
    c.execute("SELECT COUNT(*) FROM custom_flows")
    if c.fetchone()[0] == 0:
        flow_seeds = [
            ('BatteryLab_Tasks', 'TL-2', 1, 'Pre-Test Check'),
            ('BatteryLab_Tasks', 'TL-2', 2, 'Pre-Capacity'),
            ('BatteryLab_Tasks', 'TL-2', 3, 'Thermal Cycling'),
            ('BatteryLab_Tasks', 'TL-9', 1, 'Pre-Test Inspection'),
            ('BatteryLab_Tasks', 'TL-9', 2, 'Life Cycle Run'),
            ('BatteryLab_Tasks', 'TL-9', 3, 'Post Capacity Check')
        ]
        c.executemany("INSERT INTO custom_flows (lab_name, flow_name, step_order, step_name) VALUES (?, ?, ?, ?)", flow_seeds)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully!")
