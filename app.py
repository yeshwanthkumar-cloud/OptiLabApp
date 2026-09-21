from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from database import init_db, get_connection

app = Flask(__name__, template_folder='.')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

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

# -----------------------------------------------------------------------------
# ROSTER APIS (ROBUST & FAST)
# -----------------------------------------------------------------------------
@app.route('/api/get_roster_matrix/<lab_name>/<year_month>')
def get_roster_matrix(lab_name, year_month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM monthly_roster_matrix WHERE lab_name = ? AND year_month = ?", (lab_name, year_month))
    rows = c.fetchall()
    
    # If month has no entries, seed automatically from associates master
    if not rows:
        c.execute("SELECT associate_name FROM associates_master WHERE lab_name = ?", (lab_name,))
        assocs = c.fetchall()
        for a in assocs:
            c.execute("INSERT INTO monthly_roster_matrix (lab_name, operator_name, year_month) VALUES (?, ?, ?)",
                      (lab_name, a[0], year_month))
        conn.commit()
        c.execute("SELECT * FROM monthly_roster_matrix WHERE lab_name = ? AND year_month = ?", (lab_name, year_month))
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
    c.execute(f"UPDATE monthly_roster_matrix SET {day_col} = ? WHERE lab_name = ? AND operator_name = ? AND year_month = ?",
              (data.get('status_code'), data.get('lab_name'), data.get('operator_name'), data.get('year_month', '2026-09')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/delete_associate', methods=['POST'])
def delete_associate():
    data = request.json
    lab_name = data.get('lab_name')
    name = data.get('operator_name')
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM associates_master WHERE lab_name = ? AND associate_name = ?", (lab_name, name))
    c.execute("DELETE FROM monthly_roster_matrix WHERE lab_name = ? AND operator_name = ?", (lab_name, name))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/edit_associate_name', methods=['POST'])
def edit_associate_name():
    data = request.json
    lab_name = data.get('lab_name')
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE associates_master SET associate_name = ? WHERE lab_name = ? AND associate_name = ?", (new_name, lab_name, old_name))
    c.execute("UPDATE monthly_roster_matrix SET operator_name = ? WHERE lab_name = ? AND operator_name = ?", (new_name, lab_name, old_name))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/clone_roster', methods=['POST'])
def clone_roster():
    data = request.json
    lab_name = data.get('lab_name')
    curr_month = data.get('current_month')
    next_month = data.get('next_month')

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM monthly_roster_matrix WHERE lab_name = ? AND year_month = ?", (lab_name, curr_month))
    rows = c.fetchall()

    for r in rows:
        c.execute("DELETE FROM monthly_roster_matrix WHERE lab_name = ? AND operator_name = ? AND year_month = ?", (lab_name, r[2], next_month))
        vals = [lab_name, r[2], next_month] + list(r[4:])
        c.execute("""
            INSERT INTO monthly_roster_matrix 
            (lab_name, operator_name, year_month, day_1, day_2, day_3, day_4, day_5, day_6, day_7, day_8, day_9, day_10, day_11, day_12, day_13, day_14, day_15, day_16, day_17, day_18, day_19, day_20, day_21, day_22, day_23, day_24, day_25, day_26, day_27, day_28, day_29, day_30, day_31)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vals)

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
