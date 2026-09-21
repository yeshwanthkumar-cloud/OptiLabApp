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
# GET TASKS & STATIONS
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
            "chamber_id": r[17], "cycler_id": r[18], "slot_id": r[19] if len(r) > 19 else 'Slot A',
            "progress_percent": r[20] if len(r) > 20 else '0%',
            "status": r[21] if len(r) > 21 else 'To Do',
            "background": r[22] if len(r) > 22 else '',
            "observations": r[23] if len(r) > 23 else '',
            "target_end_date": r[24] if len(r) > 24 else '2026-11-01',
            "stoppage_reason": r[25] if len(r) > 25 else ''
        })
    return jsonify(tasks)

@app.route('/api/get_stations/<lab_name>')
def get_stations(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, station_code, display_name, station_type, room_zone, grafana_url FROM equipment_stations WHERE lab_name = ?", (lab_name,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "station_code": r[1], "display_name": r[2], "station_type": r[3], "room_zone": r[4], "grafana_url": r[5]} for r in rows])

@app.route('/api/add_station', methods=['POST'])
def add_station():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO equipment_stations (lab_name, station_code, display_name, station_type, room_zone, grafana_url) VALUES (?, ?, ?, ?, ?, ?)",
              (data.get('lab_name'), data.get('station_code'), data.get('display_name'), data.get('station_type', 'Chamber'), data.get('room_zone', 'Room-1'), data.get('grafana_url', 'https://grafana.com')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    lab_name = data.get('lab_name')
    bin_pack = data.get('bin_pack')
    dvp_name = data.get('dvp_name')
    category = data.get('category', '450 Pack')
    trf_id = data.get('trf_id', '-')
    priority = data.get('priority', 'P2')
    sprint_id = data.get('sprint_id', 'Sprint 27.2.1')
    lead_engineer = data.get('lead_engineer', 'Raj Kumar')
    target_shift = data.get('target_shift', 'Unassigned')
    assign_date = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    background = data.get('background', '')
    target_end_date = data.get('target_end_date', '2026-11-01')
    steps_list = data.get('steps', [])

    conn = get_connection()
    c = conn.cursor()
    master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
    
    c.execute("""
        INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, "", lab_name, bin_pack, dvp_name, category, trf_id, priority, sprint_id,
        lead_engineer, "Unassigned", "Unassigned", target_shift, assign_date, 0, 0, "Steps", "Unassigned", "Unassigned", "Slot A", "0%",
        "Running", background, f"[Objective]: {dvp_name}", target_end_date, ""
    ))

    for idx, step in enumerate(steps_list):
        sub_id = f"SUB-{master_id.replace('TSK-','')}-{idx+1}"
        c.execute("""
            INSERT INTO master_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sub_id, master_id, lab_name, bin_pack, f"{idx+1}. {step.get('name')}", category, trf_id, priority, sprint_id,
            lead_engineer, "Unassigned", "Unassigned", target_shift, assign_date, int(step.get('target', 10)), 0, step.get('unit', 'Hours'), "Chamber-1", "EA Cycler #1", "Slot A", "0%",
            "To Do", background, "", target_end_date, ""
        ))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "master_id": master_id})

@app.route('/api/start_test', methods=['POST'])
def start_test():
    data = request.json
    task_id = data.get('task_id')
    chamber_id = data.get('chamber_id', 'Chamber-1')
    cycler_id = data.get('cycler_id', 'EA Cycler #1')
    slot_id = data.get('slot_id', 'Slot A')
    operator = data.get('operator', 'Technician')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE master_tasks SET status = 'Running', chamber_id = ?, cycler_id = ?, slot_id = ? WHERE task_id = ?",
              (chamber_id, cycler_id, slot_id, task_id))
    
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, data.get('lab_name'), data.get('shift'), task_id, operator, f"Started Test on {chamber_id} ({slot_id})", f"Station assigned: {chamber_id} - {cycler_id}"))
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
    stoppage_reason = data.get('stoppage_reason', '')
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

        c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, progress_percent = ?, observations = ?, stoppage_reason = ? WHERE task_id = ?",
                  (new_units, final_status, pct, updated_obs, stoppage_reason, task_id))
        
        c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (timestamp, lab, shift, task_id, operator, f"Logged +{added_units} units. Status: {final_status}", f"{observation_text} {('Stoppage: ' + stoppage_reason) if stoppage_reason else ''}"))

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
            "id": r[0], "lab_name": r[1], "operator_name": r[2], "year_month": r[3], "days": days_dict
        })
    return jsonify(matrix)

@app.route('/api/update_roster_day', methods=['POST'])
def update_roster_day():
    data = request.json
    day_col = f"day_{data.get('day_num')}"
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE monthly_roster_matrix SET {day_col} = ? WHERE lab_name = ? AND operator_name = ?",
              (data.get('status_code'), data.get('lab_name'), data.get('operator_name')))
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
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO associates_master (lab_name, associate_name, role_title) VALUES (?, ?, ?)", (data.get('lab_name'), data.get('name'), data.get('role', 'Technician')))
    c.execute("INSERT INTO monthly_roster_matrix (lab_name, operator_name, year_month) VALUES (?, ?, ?)", (data.get('lab_name'), data.get('name'), "2026-09"))
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

@app.route('/api/attendance_punch', methods=['POST'])
def attendance_punch():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO attendance_ledger (timestamp, operator, shift, lab_name, punch_type, s5_verified, s5_score) VALUES (?, ?, ?, ?, ?, 1, ?)",
              (timestamp, data.get('operator'), data.get('shift', 'Shift A'), data.get('lab_name'), data.get('punch_type'), data.get('s5_score', 100)))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "timestamp": timestamp})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
