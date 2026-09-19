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
# GET TASKS & SCHEMATIC DATA
# -----------------------------------------------------------------------------
@app.route('/api/tasks/<lab_name>')
def get_tasks(lab_name):
    conn = get_connection()
    c = conn.cursor()
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
            "chamber_id": r[17], "cycler_id": r[18], "progress_percent": r[19],
            "status": r[20], "background": r[21], "observations": r[22], "target_end_date": r[23]
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
    background = data.get('background', '')
    target_end_date = data.get('target_end_date', '2026-11-01')
    selected_flow = data.get('flow_name', 'CUSTOM')

    conn = get_connection()
    c = conn.cursor()
    master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
    
    c.execute("""
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, "", lab_name, bin_pack, dvp_name, category, trf_id, priority, sprint_id,
        "Raj Kumar", "Unassigned", "Unassigned", target_shift, assign_date, 0, 0, "Steps", "Unassigned", "Unassigned", "0%",
        "Running", background, f"[Objective]: {dvp_name}", target_end_date
    ))

    if selected_flow != 'CUSTOM':
        c.execute("SELECT step_order, step_name FROM custom_flows WHERE lab_name = ? AND flow_name = ? ORDER BY step_order", (lab_name, selected_flow))
        flow_steps = c.fetchall()
        for step_order, step_name in flow_steps:
            sub_id = f"SUB-{master_id.replace('TSK-','')}-{step_order}"
            c.execute("""
                INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_id, master_id, lab_name, bin_pack, f"{step_order}. {step_name}", category, trf_id, priority, sprint_id,
                "Raj Kumar", "Unassigned", "Unassigned", target_shift, assign_date, 10, 0, "Hours", "Chamber-1", "EA Cycler #1", "0%",
                "To Do", background, "", target_end_date
            ))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "master_id": master_id})

@app.route('/api/delete_step', methods=['POST'])
def delete_step():
    data = request.json
    subtask_id = data.get('subtask_id')
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM master_tasks WHERE task_id = ?", (subtask_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/assign_subtask_step', methods=['POST'])
def assign_subtask_step():
    data = request.json
    subtask_id = data.get('subtask_id')
    assign_date = data.get('assign_date')
    target_shift = data.get('target_shift')
    shift_incharge = data.get('shift_incharge')
    chamber_id = data.get('chamber_id')
    cycler_id = data.get('cycler_id')
    target_units = int(data.get('target_units', 10))
    unit_type = data.get('unit_type', 'Hours')

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE master_tasks 
        SET assign_date = ?, target_shift = ?, shift_incharge = ?, chamber_id = ?, cycler_id = ?, target_units = ?, unit_type = ?, status = 'Running' 
        WHERE task_id = ?
    """, (assign_date, target_shift, shift_incharge, chamber_id, cycler_id, target_units, unit_type, subtask_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_roster_matrix/<lab_name>')
def get_roster_matrix(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM monthly_roster_matrix WHERE lab_name = ?", (lab_name,))
    rows = c.fetchall()
    conn.close()
    
    matrix = []
    for r in rows:
        days_dict = {}
        for d in range(1, 32):
            days_dict[f"day_{d}"] = r[d+3] if (d+3) < len(r) else 'A'
        matrix.append({
            "id": r[0],
            "lab_name": r[1],
            "operator_name": r[2],
            "year_month": r[3],
            "days": days_dict
        })
    return jsonify(matrix)

@app.route('/api/update_roster_day', methods=['POST'])
def update_roster_day():
    data = request.json
    lab_name = data.get('lab_name')
    operator_name = data.get('operator_name')
    day_col = f"day_{data.get('day_num')}"
    new_code = data.get('status_code')

    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE monthly_roster_matrix SET {day_col} = ? WHERE lab_name = ? AND operator_name = ?",
              (new_code, lab_name, operator_name))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/get_masters/<lab_name>')
def get_masters(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT associate_name, role_title FROM associates_master WHERE lab_name = ?", (lab_name,))
    rows = c.fetchall()
    associates = [r[0] for r in rows]
    incharges = [r[0] for r in rows if r[1] == 'Shift Incharge'] or associates
    
    c.execute("SELECT component_name FROM components_master WHERE lab_name = ?", (lab_name,))
    components = [r[0] for r in c.fetchall()]
    conn.close()
    
    return jsonify({"associates": associates, "incharges": incharges, "components": components})

@app.route('/api/add_associate', methods=['POST'])
def add_associate():
    data = request.json
    lab_name = data.get('lab_name')
    name = data.get('name')
    role = data.get('role', 'Technician')

    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO associates_master (lab_name, associate_name, role_title) VALUES (?, ?, ?)", (lab_name, name, role))
    c.execute("INSERT INTO monthly_roster_matrix (lab_name, operator_name, year_month) VALUES (?, ?, ?)", (lab_name, name, "2026-09"))
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

@app.route('/api/start_test', methods=['POST'])
def start_test():
    data = request.json
    task_id = data.get('task_id')
    operator = data.get('operator', 'Floor Associate')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE master_tasks SET status = 'Running' WHERE task_id = ?", (task_id,))
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, data.get('lab_name'), data.get('shift'), task_id, operator, "Started Test Run", "Test formally started."))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/update_progress', methods=['POST'])
def update_progress():
    data = request.json
    task_id = data.get('task_id')
    added_units = int(data.get('completed_units', 0))
    status = data.get('status')
    observation_text = data.get('observation_text', '')
    operator = data.get('operator', 'Technician')
    shift = data.get('shift', 'Shift A')
    lab = data.get('lab_name')

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT completed_units, target_units, observations FROM master_tasks WHERE task_id = ?", (task_id,))
    r = c.fetchone()
    
    if r:
        new_units = r[0] + added_units
        target = r[1]
        existing_obs = r[2] or ""
        
        final_status = "Completed" if (target > 0 and new_units >= target) else status
        pct = f"{int((new_units/target)*100)}%" if target > 0 else "100%"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        updated_obs = f"{existing_obs}\n[{timestamp} - {operator} ({shift})]: {observation_text}".strip()

        c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, progress_percent = ?, observations = ? WHERE task_id = ?",
                  (new_units, final_status, pct, updated_obs, task_id))
        
        c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (timestamp, lab, shift, task_id, operator, f"Logged +{added_units} units. Status: {final_status}", observation_text))

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

@app.route('/api/get_task_history/<lab_name>')
def get_task_history(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, task_id, operator, shift, action, notes FROM audit_log WHERE lab_name = ? ORDER BY id DESC LIMIT 100", (lab_name,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{"timestamp": r[0], "task_id": r[1], "operator": r[2], "shift": r[3], "action": r[4], "notes": r[5]} for r in rows])

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
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task_id, "EXTRA", lab_name, "AD-HOC", dvp_name, "Ad-Hoc Task", "-", "P2", "27.2.1",
        "Floor Eng", incharge, "Unassigned", target_shift, assign_date, 1, 0, "Hours", "Chamber-1", "EA Cycler #1", "0%",
        "To Do", "Extra task added during shift", "", assign_date
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/add_shift_note', methods=['POST'])
def add_shift_note():
    data = request.json
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, data.get('lab_name'), data.get('shift'), "SHIFT-NOTE", data.get('operator', 'Floor Team'), "Shift Message Logged", data.get('note')))
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

@app.route('/api/get_flows/<lab_name>')
def get_flows(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT flow_name, step_order, step_name FROM custom_flows WHERE lab_name = ? ORDER BY flow_name, step_order", (lab_name,))
    rows = c.fetchall()
    conn.close()
    flows = {}
    for flow_name, step_order, step_name in rows:
        if flow_name not in flows: flows[flow_name] = []
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
    return jsonify({"success": True, "timestamp": timestamp})

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
