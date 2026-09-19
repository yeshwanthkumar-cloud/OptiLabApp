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
    
    # Update Task Metric
    c.execute("UPDATE master_tasks SET completed_units = ?, status = ?, observations = ? WHERE task_id = ?",
              (units, status, reason, task_id))
    
    # Log Audit Excuse
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO audit_log (timestamp, lab_name, shift, task_id, operator, action, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, lab, shift, task_id, operator, f"Updated status to {status}", reason))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Progress and justification logged!"})

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
