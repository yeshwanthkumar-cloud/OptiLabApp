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
            unit_type TEXT,
            equipment_id TEXT,
            progress_percent TEXT,
            status TEXT,
            background TEXT,
            observations TEXT
        )
    ''')
    
    # Dynamic Test Flows Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS custom_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            flow_name TEXT,
            step_order INTEGER,
            step_name TEXT
        )
    ''')

    # Attendance & 5S Ledger
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

    # Seed Initial Default Flows if empty
    c.execute("SELECT COUNT(*) FROM custom_flows")
    if c.fetchone()[0] == 0:
        default_flows = [
            ('BatteryLab_Tasks', 'TL-9 Life Cycle', 1, 'Pre-Test Inspection & Capacity'),
            ('BatteryLab_Tasks', 'TL-9 Life Cycle', 2, 'Thermal Life Cycle Run'),
            ('BatteryLab_Tasks', 'TL-9 Life Cycle', 3, 'Post-Capacity Check'),
            ('BatteryLab_Tasks', 'TL-9 Life Cycle', 4, 'Air Leak & Insulation Test'),
            ('CellLab_Tasks', 'Cell Formation Standard', 1, 'Electrolyte Wetting'),
            ('CellLab_Tasks', 'Cell Formation Standard', 2, 'Initial C-Rate Formation'),
            ('CellLab_Tasks', 'Cell Formation Standard', 3, 'Degassing & Sealing'),
            ('Vibration_Tasks', 'Standard Vibration Flow', 1, 'DUT Mounting & Sensors'),
            ('Vibration_Tasks', 'Standard Vibration Flow', 2, 'X-Axis Sine Sweep'),
            ('Vibration_Tasks', 'Standard Vibration Flow', 3, 'Y-Axis Random Run'),
            ('Vibration_Tasks', 'Standard Vibration Flow', 4, 'Z-Axis Shock Test'),
            ('EELab_Tasks', 'BMS Stress Validation', 1, 'CAN Baud Rate Check'),
            ('EELab_Tasks', 'BMS Stress Validation', 2, 'High Current Discharge Run'),
            ('EELab_Tasks', 'BMS Stress Validation', 3, 'Thermal Cutoff Verification')
        ]
        c.executemany("INSERT INTO custom_flows (lab_name, flow_name, step_order, step_name) VALUES (?, ?, ?, ?)", default_flows)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully with Equipment Mapping & Dynamic Flows!")
