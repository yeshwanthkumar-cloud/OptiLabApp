import sqlite3

def get_connection():
    return sqlite3.connect('opti_lab_master.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Master Tasks & Nested Subtasks Table
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
            chamber_id TEXT,
            cycler_id TEXT,
            progress_percent TEXT,
            status TEXT,
            background TEXT,
            observations TEXT,
            target_end_date TEXT
        )
    ''')

    # Custom Dynamic Test Flows
    c.execute('''
        CREATE TABLE IF NOT EXISTS custom_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            flow_name TEXT,
            step_order INTEGER,
            step_name TEXT
        )
    ''')

    # Registered Associates Master
    c.execute('''
        CREATE TABLE IF NOT EXISTS associates_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            associate_name TEXT,
            role_title TEXT DEFAULT 'Associate'
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

    # Monthly Grid Shift Roster (Days 1 to 31)
    c.execute('''
        CREATE TABLE IF NOT EXISTS monthly_roster_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            operator_name TEXT,
            year_month TEXT,
            day_1 TEXT DEFAULT 'A', day_2 TEXT DEFAULT 'A', day_3 TEXT DEFAULT 'A', day_4 TEXT DEFAULT 'A', day_5 TEXT DEFAULT 'A',
            day_6 TEXT DEFAULT 'O', day_7 TEXT DEFAULT 'O', day_8 TEXT DEFAULT 'B', day_9 TEXT DEFAULT 'B', day_10 TEXT DEFAULT 'B',
            day_11 TEXT DEFAULT 'B', day_12 TEXT DEFAULT 'B', day_13 TEXT DEFAULT 'O', day_14 TEXT DEFAULT 'O', day_15 TEXT DEFAULT 'C',
            day_16 TEXT DEFAULT 'C', day_17 TEXT DEFAULT 'C', day_18 TEXT DEFAULT 'C', day_19 TEXT DEFAULT 'C', day_20 TEXT DEFAULT 'O',
            day_21 TEXT DEFAULT 'O', day_22 TEXT DEFAULT 'A', day_23 TEXT DEFAULT 'A', day_24 TEXT DEFAULT 'A', day_25 TEXT DEFAULT 'A',
            day_26 TEXT DEFAULT 'A', day_27 TEXT DEFAULT 'O', day_28 TEXT DEFAULT 'O', day_29 TEXT DEFAULT 'A', day_30 TEXT DEFAULT 'A', day_31 TEXT DEFAULT 'A'
        )
    ''')

    # Attendance Ledger
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

    # Audit History Log
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

    # Seed Default Associates if empty
    c.execute("SELECT COUNT(*) FROM associates_master")
    if c.fetchone()[0] == 0:
        assoc_seeds = [
            ('BatteryLab_Tasks', 'Sathya', 'Technician'),
            ('BatteryLab_Tasks', 'Sanjay', 'Technician'),
            ('BatteryLab_Tasks', 'Yosvaraj', 'Technician'),
            ('BatteryLab_Tasks', 'Bharani', 'Technician'),
            ('BatteryLab_Tasks', 'Praveen kumar', 'Shift Incharge'),
            ('BatteryLab_Tasks', 'Raja', 'Shift Incharge'),
            ('BatteryLab_Tasks', 'Riyaz', 'Shift Incharge'),
            ('CellLab_Tasks', 'Arun', 'Technician'),
            ('CellLab_Tasks', 'Karthik', 'Technician'),
            ('Vibration_Tasks', 'Vignesh', 'Technician'),
            ('EELab_Tasks', 'Deepak', 'Technician')
        ]
        c.executemany("INSERT INTO associates_master (lab_name, associate_name, role_title) VALUES (?, ?, ?)", assoc_seeds)

    # Seed Default Roster Matrix for Battery Lab
    c.execute("SELECT COUNT(*) FROM monthly_roster_matrix")
    if c.fetchone()[0] == 0:
        roster_seeds = [
            ('BatteryLab_Tasks', 'Sathya', '2026-09'),
            ('BatteryLab_Tasks', 'Sanjay', '2026-09'),
            ('BatteryLab_Tasks', 'Yosvaraj', '2026-09'),
            ('BatteryLab_Tasks', 'Bharani', '2026-09'),
            ('BatteryLab_Tasks', 'Praveen kumar', '2026-09'),
            ('BatteryLab_Tasks', 'Raja', '2026-09')
        ]
        c.executemany("INSERT INTO monthly_roster_matrix (lab_name, operator_name, year_month) VALUES (?, ?, ?)", roster_seeds)

    # Seed Default Components if empty
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
