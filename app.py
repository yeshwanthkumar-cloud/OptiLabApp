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
# DYNAMIC TEST FLOW BUILDER ENDPOINTS
# -----------------------------------------------------------------------------
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
    lab_name = data.get('lab_name')
    flow_name = data.get('flow_name')
    steps = data.get('steps', [])

    conn = get_connection()
    c = conn.cursor()
    for idx, step_name in enumerate(steps):
        c.execute("INSERT INTO custom_flows (lab_name, flow_name, step_order, step_name) VALUES (?, ?, ?, ?)",
                  (lab_name, flow_name, idx + 1, step_name.strip()))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# -----------------------------------------------------------------------------
# MASTER TASK CREATION & RETRIEVAL
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
            "completed_units": r[14], "unit_type": r[15], "equipment_id": r[16],
            "progress_percent": r[17], "status": r[18], "background": r[19], "observations": r[20]
        })
    return jsonify(tasks)

@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    lab_name = data.get('lab_name')
    bin_pack = data.get('bin_pack')
    dvp_name = data.get('dvp_name')
    category = data.get('category', 'General Component')
    trf_id = data.get('trf_id', '')
    priority = data.get('priority', 'P2')
    target_shift = data.get('target_shift', 'Shift A')
    target_units = int(data.get('target_units', 100))
    unit_type = data.get('unit_type', 'Cycles')
    equipment_id = data.get('equipment_id', 'Unassigned')
    background = data.get('background', '')
    selected_flow = data.get('flow_name', 'CUSTOM')

    conn = get_connection()
    c = conn.cursor()
    
    master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
    
    c.execute("""
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, "", lab_name, bin_pack, dvp_name, category, trf_id, priority, "27.2.1",
        "Lead Engineer", "Shift Incharge", "Unassigned", target_shift, target_units, 0, unit_type, equipment_id, "0%",
        "Running", background, f"[Objective]: {dvp_name}"
    ))

    if selected_flow != 'CUSTOM':
        c.execute("SELECT step_order, step_name FROM custom_flows WHERE lab_name = ? AND flow_name = ? ORDER BY step_order", (lab_name, selected_flow))
        flow_steps = c.fetchall()
        for step_order, step_name in flow_steps:
            sub_id = f"SUB-{master_id.replace('TSK-','')}-{step_order}"
            c.execute("""
                INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_id, master_id, lab_name, bin_pack, f"{step_order}. {step_name}", category, trf_id, priority, "27.2.1",
                "Lead Engineer", "Shift Incharge", "Unassigned", target_shift, target_units, 0, unit_type, equipment_id, "0%",
                "To Do", background, ""
            ))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "master_id": master_id})

# -----------------------------------------------------------------------------
# PROGRESS UPDATES & AUTOMATIC ROLLOVER
# -----------------------------------------------------------------------------
@app.route('/api/update_progress', methods=['POST'])
def update_progress():
    data = request.json
    task_id = data.get('task_id')
    units = int(data.get('completed_units', 0))
    status = data.get('status')
    reason = data.get('reason', '')
    operator = data.get('operator', 'Technician')
    shift = data.get('shift', 'Shift A')
    lab = data.get('lab_name')

    conn = get_connection()
    c = conn.cursor()
    
    next_shift_map = {"Shift A": "Shift B", "Shift B": "Shift C", "Shift C": "Shift A"}
    target_shift = shift
    if status in ['Running', 'Awaiting Resource']:
        target_shift = next_shift_map.get(shift, shift)

    c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, observations = ?, target_shift = ? WHERE task_id = ?",
              (units, status, reason, target_shift, task_id))
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, lab, shift, task_id, operator, f"Updated progress: {units} units. Status: {status}", reason))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/assign_associate', methods=['POST'])
def assign_associate():
    data = request.json
    task_id = data.get('task_id')
    associate = data.get('associate')
    equipment_id = data.get('equipment_id')
    
    conn = get_connection()
    c = conn.cursor()
    if equipment_id:
        c.execute("UPDATE master_tasks SET assigned_associate = ?, equipment_id = ?, status = 'Running' WHERE task_id = ?", (associate, equipment_id, task_id))
    else:
        c.execute("UPDATE master_tasks SET assigned_associate = ?, status = 'Running' WHERE task_id = ?", (associate, task_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# -----------------------------------------------------------------------------
# ATTENDANCE & 5S LOGGING
# -----------------------------------------------------------------------------
@app.route('/api/attendance_punch', methods=['POST'])
def attendance_punch():
    data = request.json
    operator = data.get('operator')
    punch_type = data.get('punch_type')
    shift = data.get('shift', 'Shift A')
    lab_name = data.get('lab_name')
    s5_verified = 1 if data.get('s5_verified') else 0

    conn = get_connection()
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO attendance_ledger (timestamp, operator, shift, lab_name, punch_type, s5_verified) VALUES (?, ?, ?, ?, ?, ?)",
              (timestamp, operator, shift, lab_name, punch_type, s5_verified))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "timestamp": timestamp})

@app.route('/api/get_attendance/<lab_name>')
def get_attendance(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, operator, shift, punch_type, s5_verified FROM attendance_ledger WHERE lab_name = ? ORDER BY id DESC LIMIT 50", (lab_name,))
    rows = c.fetchall()
    conn.close()
    
    logs = [{"timestamp": r[0], "operator": r[1], "shift": r[2], "punch_type": r[3], "s5_verified": r[4]} for r in rows]
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
