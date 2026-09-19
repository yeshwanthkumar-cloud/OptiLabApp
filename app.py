from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from database import init_db, get_connection

app = Flask(__name__, template_folder='.')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

# -----------------------------------------------------------------------------
# GET DATA FOR ACTIVE LAB
# -----------------------------------------------------------------------------
@app.route('/api/tasks/<lab_name>')
def get_tasks(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_tasks WHERE lab_name = ?", (lab_name,))
    rows = c.fetchall()
    conn.close()
    
    tasks = []
    for r in rows:
        tasks.append({
            "task_id": r[0], "parent_id": r[1], "lab_name": r[2], "bin_pack": r[3],
            "dvp_name": r[4], "category": r[5], "trf_id": r[6], "priority": r[7],
            "sprint_id": r[8], "lead_engineer": r[9], "shift_incharge": r[10],
            "assigned_associate": r[11], "target_shift": r[12], "target_units": r[13],
            "completed_units": r[14], "progress_percent": r[15], "status": r[16],
            "observations": r[17]
        })
    return jsonify(tasks)

# -----------------------------------------------------------------------------
# CREATE NEW MASTER DVP TASK & AUTOMATED BLUEPRINT STEPS
# -----------------------------------------------------------------------------
@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    lab_name = data.get('lab_name', 'BatteryLab_Tasks')
    bin_pack = data.get('bin_pack')
    dvp_name = data.get('dvp_name')
    category = data.get('category', 'General')
    trf_id = data.get('trf_id', '')
    priority = data.get('priority', 'P2')
    sprint_id = data.get('sprint_id', '27.2.1')
    lead_eng = data.get('lead_engineer', 'Yeshwanth')
    target_shift = data.get('target_shift', 'Shift A')
    objective = data.get('objective', '')
    blueprint = data.get('blueprint', 'CUSTOM')

    conn = get_connection()
    c = conn.cursor()
    
    master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
    
    c.execute("""
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, "", lab_name, bin_pack, dvp_name, category, trf_id, priority, sprint_id,
        lead_eng, "Praveen kumar", "Unassigned", target_shift, 100, 0, "0%",
        "Running", f"[Objective]: {objective}"
    ))

    # Auto-generate blueprint subtasks if selected
    blueprint_steps = {
        "TL-1 Profile": ["1. Pre-Test Check", "2. Pre-Capacity", "3. Random Vibration", "4. Post Capacity", "5. Air Leak Test"],
        "TL-2 Thermal": ["1. Pre-Test Check", "2. Thermal Cycling", "3. Post Capacity", "4. Air Leak Test"],
        "TL-9 Life Cycle": ["1. Pre-Test Check", "2. Life Cycle Run", "3. Post Capacity", "4. Air Leak Test"],
        "Cell Formation": ["1. Electrolyte Wetting", "2. Initial C-Rate Formation", "3. Degassing Stamping"],
        "Vibration Flow": ["1. Pre-Test Photos", "2. DUT Mounting", "3. X-Axis Run", "4. Y-Axis Run", "5. Z-Axis Run"],
        "CAN Validation": ["1. Baud Validation", "2. Frame Stress Run", "3. Diagnostic Verification"]
    }

    if blueprint in blueprint_steps:
        for idx, step_name in enumerate(blueprint_steps[blueprint]):
            sub_id = f"SUB-{master_id.replace('TSK-','')}-{idx+1}"
            c.execute("""
                INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_id, master_id, lab_name, bin_pack, step_name, category, trf_id, priority, sprint_id,
                lead_eng, "Praveen kumar", "Unassigned", target_shift, 100 if "Cycle" in step_name else 1, 0, "0%",
                "To Do", ""
            ))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "master_id": master_id})

# -----------------------------------------------------------------------------
# LOG ATTENDANCE PUNCHES
# -----------------------------------------------------------------------------
@app.route('/api/attendance_punch', methods=['POST'])
def attendance_punch():
    data = request.json
    operator = data.get('operator')
    punch_type = data.get('punch_type')
    shift = data.get('shift', 'Shift A')
    lab_name = data.get('lab_name')

    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operator TEXT,
            shift TEXT,
            lab_name TEXT,
            punch_type TEXT
        )
    ''')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO attendance_ledger (timestamp, operator, shift, lab_name, punch_type) VALUES (?, ?, ?, ?, ?)",
              (timestamp, operator, shift, lab_name, punch_type))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "timestamp": timestamp})

@app.route('/api/get_attendance/<lab_name>')
def get_attendance(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operator TEXT,
            shift TEXT,
            lab_name TEXT,
            punch_type TEXT
        )
    ''')
    c.execute("SELECT timestamp, operator, shift, punch_type FROM attendance_ledger WHERE lab_name = ? ORDER BY id DESC LIMIT 50", (lab_name,))
    rows = c.fetchall()
    conn.close()
    
    logs = [{"timestamp": r[0], "operator": r[1], "shift": r[2], "punch_type": r[3]} for r in rows]
    return jsonify(logs)

# -----------------------------------------------------------------------------
# UPDATE PROGRESS WITH MANDATORY JUSTIFICATION
# -----------------------------------------------------------------------------
@app.route('/api/update_progress', methods=['POST'])
def update_progress():
    data = request.json
    task_id = data.get('task_id')
    units = data.get('completed_units')
    status = data.get('status')
    reason = data.get('reason', '')
    operator = data.get('operator', 'Technician')
    shift = data.get('shift', 'Shift A')
    lab = data.get('lab_name', 'BatteryLab_Tasks')

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, observations = ? WHERE task_id = ?",
              (units, status, reason, task_id))
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, lab, shift, task_id, operator, f"Updated status to {status}", reason))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/assign_associate', methods=['POST'])
def assign_associate():
    data = request.json
    task_id = data.get('task_id')
    associate = data.get('associate')
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE master_tasks SET assigned_associate = ?, status = 'Running' WHERE task_id = ?", (associate, task_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
