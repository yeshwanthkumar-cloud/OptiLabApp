import sqlite3

def init_db():
    conn = sqlite3.connect('lab_governance.db')
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
            assign_date TEXT,
            target_units INTEGER,
            completed_units INTEGER,
            unit_type TEXT,
            chamber_id TEXT,
            cycler_id TEXT,
            slot_id TEXT,
            progress_percent TEXT,
            status TEXT,
            background TEXT,
            observations TEXT,
            target_end_date TEXT,
            stoppage_reason TEXT
        )
    ''')

    # Equipment Stations Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            station_code TEXT,
            display_name TEXT,
            station_type TEXT,
            room_zone TEXT,
            grafana_url TEXT
        )
    ''')

    # Monthly Roster Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS monthly_roster_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            operator_name TEXT,
            year_month TEXT,
            day_1 TEXT, day_2 TEXT, day_3 TEXT, day_4 TEXT, day_5 TEXT,
            day_6 TEXT, day_7 TEXT, day_8 TEXT, day_9 TEXT, day_10 TEXT,
            day_11 TEXT, day_12 TEXT, day_13 TEXT, day_14 TEXT, day_15 TEXT,
            day_16 TEXT, day_17 TEXT, day_18 TEXT, day_19 TEXT, day_20 TEXT,
            day_21 TEXT, day_22 TEXT, day_23 TEXT, day_24 TEXT, day_25 TEXT,
            day_26 TEXT, day_27 TEXT, day_28 TEXT, day_29 TEXT, day_30 TEXT, day_31 TEXT
        )
    ''')

    # Associates Master Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS associates_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            associate_name TEXT,
            role_title TEXT
        )
    ''')

    # Components Master Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS components_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            component_name TEXT
        )
    ''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect('lab_governance.db')
