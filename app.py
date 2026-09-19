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
# GET TASKS & SEED BATTERY LAB DATA
# -----------------------------------------------------------------------------
@app.route('/api/tasks/<lab_name>')
def get_tasks(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_tasks WHERE lab_name = ? ORDER BY CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, task_id", (lab_name,))
    rows = c.fetchall()
    
    if len(rows) == 0 and lab_name == 'BatteryLab_Tasks':
        sample_data = [
            ('TSK-385040', '', 'BatteryLab_Tasks', 'STB-0218', 'TL-2', '450 Pack', '-', 'P1', '27.2.1', 'Raj Kumar', 'Unassigned', 'Unassigned', 'Shift A', '2026-08-05', 100, 100, 'Cycles', 'Chamber-3', '100%', 'Awaiting Report', 'STB 14P LVPT', 'LVPT Validation', '2026-08-04'),
            ('SUB-806937', 'TSK-385040', 'BatteryLab_Tasks', 'STB-0218', '1. Pre-Test Check', '450 Pack', '-', 'P1', '27.2.1', 'Raj Kumar', 'Raja', 'Sathya', 'Shift A', '2026-08-05', 1, 1, 'Units', 'Chamber-3', '100%', 'Completed', '', '', '2026-08-04'),
            ('SUB-655622', 'TSK-385040', 'BatteryLab_Tasks', 'STB-0218', '2. Pre-Capacity', '450 Pack', '-', 'P1', '27.2.1', 'Raj Kumar', 'Praveen kumar', 'Sanjay', 'Shift A', '2026-08-05', 9, 9, 'Units', 'Chamber-3', '100%', 'Completed', '', '', '2026-08-04'),
            ('SUB-918705', 'TSK-385040', 'BatteryLab_Tasks', 'STB-0218', '3. Thermal Cycling', '450 Pack', '-', 'P1', '27.2.1', 'Raj Kumar', 'Riyaz', 'Yosvaraj', 'Shift B', '2026-08-05', 250, 250, 'Units', 'Chamber-3', '100%', 'Completed', '', '', '2026-08-04'),
            ('TSK-599727', '', 'BatteryLab_Tasks', '450-9702', 'TL-9', '450 Pack', '-', 'P1', '27.2.1', 'Raj Kumar', 'Unassigned', 'Unassigned', 'Shift A', '2026-08-05', 1000, 380, 'Cycles', 'Chamber-1', '38%', 'Running', '11P life cycle pack', 'Thermal life run', '2026-11-01'),
            ('SUB-301921', 'TSK-599727', 'BatteryLab_Tasks', '450-9702', '1. Life Cycle Run Step', '450 Pack', '-', 'P1', '27.2.1', 'Raj Kumar', 'Praveen kumar', 'Sanjay', 'Shift A', '2026-08-05', 1000, 380, 'Cycles', 'Chamber-1', '38%', 'Running', '', '', '2026-11-01')
        ]
        c.executemany("INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_data)
        conn.commit()
        c.execute("SELECT * FROM master_tasks WHERE lab_name = ? ORDER BY CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, task_id", (lab_name,))
        rows = c.fetchall()

    conn.close()
    
    tasks = []
    for r in rows:
        tasks.append({
            "task_id": r[0], "parent_id": r[1], "lab_name": r[2], "bin_pack": r[3],
            "dvp_name": r[4], "category": r[5], "trf_id": r[6], "priority": r[7],
            "sprint_id": r[8], "lead_engineer": r[9], "shift_incharge": r[10],
            "assigned_associate": r[11], "target_shift": r[12], "assign_date": r[13],
            "target_units": r[14], "completed_units": r[15], "unit_type": r[16],
            "equipment_id": r[17], "progress_percent": r[18], "status": r[19],
            "background": r[20], "observations": r[21], "target_end_date": r[22]
        })
    return jsonify(tasks)

@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    lab_name = data.get('lab_name')
    bin_pack = data.get('bin_pack')
    dvp_name = data.get('dvp_name')
    category = data.get('category', '450 Pack')
    trf_id = data.get('trf_id', '-')
    priority = data.get('priority', 'P2')
    sprint_id = data.get('sprint_id', '27.2.1')
    target_shift = data.get('target_shift', 'Shift A')
    assign_date = data.get('assign_date', datetime.now().strftime('%Y-%m-%d'))
    target_units = int(data.get('target_units', 100))
    unit_type = data.get('unit_type', 'Cycles')
    equipment_id = data.get('equipment_id', 'Chamber-1')
    background = data.get('background', '')
    target_end_date = data.get('target_end_date', '2026-11-01')
    selected_flow = data.get('flow_name', 'CUSTOM')

    conn = get_connection()
    c = conn.cursor()
    master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
    
    c.execute("""
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, "", lab_name, bin_pack, dvp_name, category, trf_id, priority, sprint_id,
        "Raj Kumar", "Unassigned", "Unassigned", target_shift, assign_date, target_units, 0, unit_type, equipment_id, "0%",
        "Running", background, f"[Objective]: {dvp_name}", target_end_date
    ))

    if selected_flow != 'CUSTOM':
        c.execute("SELECT step_order, step_name FROM custom_flows WHERE lab_name = ? AND flow_name = ? ORDER BY step_order", (lab_name, selected_flow))
        flow_steps = c.fetchall()
        for step_order, step_name in flow_steps:
            sub_id = f"SUB-{master_id.replace('TSK-','')}-{step_order}"
            c.execute("""
                INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_id, master_id, lab_name, bin_pack, f"{step_order}. {step_name}", category, trf_id, priority, sprint_id,
                "Raj Kumar", "Praveen kumar", "Unassigned", target_shift, assign_date, 100, 0, unit_type, equipment_id, "0%",
                "To Do", background, "", target_end_date
            ))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "master_id": master_id})

# -----------------------------------------------------------------------------
# SHIFT EXTRA TASK CREATION
# -----------------------------------------------------------------------------
@app.route('/api/add_extra_task', methods=['POST'])
def add_extra_task():
    data = request.json
    lab_name = data.get('lab_name')
    dvp_name = data.get('dvp_name')
    target_shift = data.get('target_shift')
    incharge = data.get('incharge', 'Shift Incharge')
    assign_date = datetime.now().strftime('%Y-%m-%d')
    task_id = f"EXT-{datetime.now().strftime('%H%M%S')}"

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task_id, "EXTRA", lab_name, "AD-HOC", dvp_name, "Ad-Hoc Task", "-", "P2", "27.2.1",
        "Floor Eng", incharge, "Unassigned", target_shift, assign_date, 1, 0, "Units", "Chamber-1", "0%",
        "To Do", "Extra task added during shift", "", assign_date
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# -----------------------------------------------------------------------------
# SHIFT MESSAGES & NOTES
# -----------------------------------------------------------------------------
@app.route('/api/add_shift_note', methods=['POST'])
def add_shift_note():
    data = request.json
    lab_name = data.get('lab_name')
    shift = data.get('shift')
    note = data.get('note')
    operator = data.get('operator', 'Floor Team')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, lab_name, shift, "SHIFT-NOTE", operator, "Shift Message Logged", note))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_shift_notes/<lab_name>/<shift>')
def get_shift_notes(lab_name, shift):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, operator, notes FROM audit_log WHERE lab_name = ? AND shift = ? AND task_id = 'SHIFT-NOTE' ORDER BY id DESC LIMIT 10", (lab_name, shift))
    rows = c.fetchall()
    conn.close()
    return jsonify([{"timestamp": r[0], "operator": r[1], "note": r[2]} for r in rows])

@app.route('/api/assign_subtask_step', methods=['POST'])
def assign_subtask_step():
    data = request.json
    subtask_id = data.get('subtask_id')
    assign_date = data.get('assign_date')
    target_shift = data.get('target_shift')
    shift_incharge = data.get('shift_incharge')

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE master_tasks 
        SET assign_date = ?, target_shift = ?, shift_incharge = ?, status = 'Running' 
        WHERE task_id = ?
    """, (assign_date, target_shift, shift_incharge, subtask_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_masters/<lab_name>')
def get_masters(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT associate_name FROM associates_master WHERE lab_name = ?", (lab_name,))
    associates = [r[0] for r in c.fetchall()]
    
    c.execute("SELECT component_name FROM components_master WHERE lab_name = ?", (lab_name,))
    components = [r[0] for r in c.fetchall()]
    conn.close()
    
    return jsonify({"associates": associates, "components": components})

@app.route('/api/add_associate', methods=['POST'])
def add_associate():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO associates_master (lab_name, associate_name) VALUES (?, ?)", (data.get('lab_name'), data.get('name')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/add_component', methods=['POST'])
def add_component():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO components_master (lab_name, component_name) VALUES (?, ?)", (data.get('lab_name'), data.get('name')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_flows/<lab_name>')
def get_flows(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT flow_name, step_order, step_name FROM custom_flows WHERE lab_name = ? ORDER BY flow_name, step_order", (lab_name,))
    rows = c.fetchall()
    conn.close()
    
    flows = {}
    for flow_name, step_order, step_name in rows:
        if flow_name not in flows:
            flows[flow_name] = []
        flows[flow_name].append({"step_order": step_order, "step_name": step_name})
    return jsonify(flows)

@app.route('/api/create_flow', methods=['POST'])
def create_flow():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    for idx, step_name in enumerate(data.get('steps', [])):
        c.execute("INSERT INTO custom_flows (lab_name, flow_name, step_order, step_name) VALUES (?, ?, ?, ?)",
                  (data.get('lab_name'), data.get('flow_name'), idx + 1, step_name.strip()))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/update_progress', methods=['POST'])
def update_progress():
    data = request.json
    task_id = data.get('task_id')
    units = int(data.get('completed_units', 0))
    status = data.get('status')
    reason = data.get('reason', '')

    conn = get_connection()
    c = conn.cursor()
    pct = f"{int((units/100)*100)}%" if units < 100 else "100%"
    c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, observations = ?, progress_percent = ? WHERE task_id = ?",
              (units, status, reason, pct, task_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/assign_associate', methods=['POST'])
def assign_associate():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE master_tasks SET assigned_associate = ?, status = 'Running' WHERE task_id = ?", (data.get('associate'), data.get('task_id')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_roster/<lab_name>')
def get_roster(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT operator_name, assigned_shift, effective_month FROM shift_roster WHERE lab_name = ?", (lab_name,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{"operator": r[0], "shift": r[1], "month": r[2]} for r in rows])

@app.route('/api/save_roster', methods=['POST'])
def save_roster():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO shift_roster (lab_name, operator_name, assigned_shift, effective_month) VALUES (?, ?, ?, ?)",
              (data.get('lab_name'), data.get('operator'), data.get('shift'), data.get('month', 'September 2026')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/attendance_punch', methods=['POST'])
def attendance_punch():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO attendance_ledger (timestamp, operator, shift, lab_name, punch_type, s5_verified) VALUES (?, ?, ?, ?, ?, 1)",
              (timestamp, data.get('operator'), data.get('shift', 'Shift A'), data.get('lab_name'), data.get('punch_type')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_attendance/<lab_name>')
def get_attendance(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, operator, shift, punch_type FROM attendance_ledger WHERE lab_name = ? ORDER BY id DESC LIMIT 50", (lab_name,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{"timestamp": r[0], "operator": r[1], "shift": r[2], "punch_type": r[3]} for r in rows])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
