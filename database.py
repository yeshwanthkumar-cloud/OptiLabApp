import sqlite3

def get_connection():
    return sqlite3.connect('opti_lab_master.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Master Tasks & Subtasks Table
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
            slot_id TEXT DEFAULT 'Slot A',
            progress_percent TEXT,
            status TEXT,
            background TEXT,
            observations TEXT,
            target_end_date TEXT,
            stoppage_reason TEXT
        )
    ''')

    # Custom Equipment Stations Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            station_code TEXT,
            display_name TEXT,
            station_type TEXT DEFAULT 'Chamber',
            room_zone TEXT DEFAULT 'Room-1',
            grafana_url TEXT DEFAULT 'https://grafana.com'
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

    # Attendance & 5S Handover Ledger
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operator TEXT,
            shift TEXT,
            lab_name TEXT,
            punch_type TEXT,
            s5_verified INTEGER DEFAULT 1,
            s5_score INTEGER DEFAULT 100
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

    # Seed Default Equipment Stations
    c.execute("SELECT COUNT(*) FROM equipment_stations")
    if c.fetchone()[0] == 0:
        station_seeds = [
            ('BatteryLab_Tasks', 'Chamber-1', 'Envisys ET-600 Chamber-1', 'Chamber', 'Room-1', 'https://grafana.com/d/et600-ch1'),
            ('BatteryLab_Tasks', 'Chamber-3', 'Envisys ET-600 Chamber-3', 'Chamber', 'Room-1', 'https://grafana.com/d/et600-ch3'),
            ('BatteryLab_Tasks', 'Chamber-4', 'Envisys ET-600 Chamber-4', 'Chamber', 'Room-1', 'https://grafana.com/d/et600-ch4'),
            ('BatteryLab_Tasks', 'EA-1', 'EA Cycler #1', 'Cycler', 'Room-1', 'https://grafana.com/d/eacycler1'),
            ('BatteryLab_Tasks', 'EA-2', 'EA Cycler #2', 'Cycler', 'Room-1', 'https://grafana.com/d/eacycler2'),
            ('BatteryLab_Tasks', 'ITECH-Cycler', 'ITECH Cycler', 'Cycler', 'Room-1', 'https://grafana.com/d/itech'),
            ('BatteryLab_Tasks', 'Channel-1', 'Bench Channel 1', 'Channel', 'Room-2', 'https://grafana.com/d/ch1'),
            ('BatteryLab_Tasks', 'Channel-2', 'Bench Channel 2', 'Channel', 'Room-2', 'https://grafana.com/d/ch2'),
            ('BatteryLab_Tasks', 'Channel-3', 'Bench Channel 3', 'Channel', 'Room-2', 'https://grafana.com/d/ch3'),
            ('BatteryLab_Tasks', 'Channel-4', 'Bench Channel 4', 'Channel', 'Room-2', 'https://grafana.com/d/ch4')
        ]
        c.executemany("INSERT INTO equipment_stations (lab_name, station_code, display_name, station_type, room_zone, grafana_url) VALUES (?, ?, ?, ?, ?, ?)", station_seeds)

    # Seed Associates
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

    # Seed Roster Matrix
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

    # Seed Component Categories Across All Labs
    c.execute("SELECT COUNT(*) FROM components_master")
    if c.fetchone()[0] == 0:
        comp_seeds = [
            ('BatteryLab_Tasks', '450 Pack'),
            ('BatteryLab_Tasks', 'DIESEL Pack'),
            ('BatteryLab_Tasks', 'EL Pack'),
            ('CellLab_Tasks', 'NMC 2170 Cell'),
            ('CellLab_Tasks', 'LFP Pouch Cell'),
            ('CellLab_Tasks', 'Prismatic Module'),
            ('Vibration_Tasks', 'Battery Mounting Bracket'),
            ('Vibration_Tasks', 'Motor Mount Jig'),
            ('EELab_Tasks', 'Master BMS Board'),
            ('EELab_Tasks', 'High Voltage Wire Harness')
        ]
        c.executemany("INSERT INTO components_master (lab_name, component_name) VALUES (?, ?)", comp_seeds)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully!")
