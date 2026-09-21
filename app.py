import os
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from database import init_db, get_connection

app = Flask(__name__, template_folder='.', static_folder='static')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks/<lab_name>')
def get_tasks(lab_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_tasks WHERE lab_name = ? ORDER BY task_id", (lab_name,))
    rows = c.fetchall()
    conn.close()
    
    tasks = []
    for r in rows:
        tasks.append({
            "task_id": r[0], "parent_id": r[1], "lab_name": r[2], "bin_pack": r[3],
            "dvp_name": r[4], "category": r[5], "trf_id": r[6], "priority": r[7],
            "sprint_id": r[8], "lead_engineer": r[9], "assigned_associate": r[11],
            "target_shift": r[12], "completed_units": r[15], "target_units": r[14],
            "unit_type": r[16], "chamber_id": r[17], "slot_id": r[19],
            "progress_percent": r[20], "status": r[21], "observations": r[23]
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
              (data.get('lab_name'), data.get('station_code'), data.get('display_name'), data.get('station_type'), data.get('room_zone', 'Room-1'), data.get('grafana_url', 'https://grafana.com')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/create_task', methods=['POST'])
def create_task():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    master_id = f"TSK-{datetime.now().strftime('%H%M%S')}"
    
    c.execute("""
        INSERT INTO master_tasks (task_id, lab_name, bin_pack, dvp_name, category, trf_id, priority, sprint_id, lead_engineer, target_shift, progress_percent, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '0%', 'To Do')
    """, (master_id, data.get('lab_name'), data.get('bin_pack'), data.get('dvp_name'), data.get('category'), data.get('trf_id', '-'), data.get('priority', 'P2'), data.get('sprint_id', 'Sprint 27.2.1'), data.get('lead_engineer', 'Raj Kumar'), data.get('target_shift', 'Shift A')))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "master_id": master_id})

@app.route('/api/get_roster_matrix/<lab_name>/<year_month>')
def get_roster_matrix(lab_name, year_month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM monthly_roster_matrix WHERE lab_name = ? AND year_month = ?", (lab_name, year_month))
    rows = c.fetchall()
    
    if not rows:
        c.execute("SELECT associate_name FROM associates_master WHERE lab_name = ?", (lab_name,))
        assocs = c.fetchall()
        for a in assocs:
            c.execute("INSERT INTO monthly_roster_matrix (lab_name, operator_name, year_month) VALUES (?, ?, ?)", (lab_name, a[0], year_month))
        conn.commit()
        c.execute("SELECT * FROM monthly_roster_matrix WHERE lab_name = ? AND year_month = ?", (lab_name, year_month))
        rows = c.fetchall()

    conn.close()
    
    matrix = []
    for r in rows:
        days_dict = {f"day_{d}": r[d+3] if (d+3) < len(r) else 'A' for d in range(1, 32)}
        matrix.append({"id": r[0], "operator_name": r[2], "days": days_dict})
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
    c.execute("SELECT associate_name FROM associates_master WHERE lab_name = ?", (lab_name,))
    associates = [r[0] for r in c.fetchall()] or ["Sathya", "Sanjay", "Bharani", "Riyaz"]
    
    c.execute("SELECT component_name FROM components_master WHERE lab_name = ?", (lab_name,))
    components = [r[0] for r in c.fetchall()] or ["450 Pack", "NMC Cell", "BMS Harness"]
    conn.close()
    return jsonify({"associates": associates, "components": components})

@app.route('/api/add_associate', methods=['POST'])
def add_associate():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO associates_master (lab_name, associate_name, role_title) VALUES (?, ?, ?)",
              (data.get('lab_name'), data.get('name'), data.get('role', 'Technician')))
    c.execute("INSERT INTO monthly_roster_matrix (lab_name, operator_name, year_month) VALUES (?, ?, '2026-09')",
              (data.get('lab_name'), data.get('name')))
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
    app.run(host='0.0.0.0', port=5000, debug=True)
