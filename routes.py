import sqlite3
from flask import session, render_template, request, redirect, url_for, flash, Response, current_app
from database.database import get_db_connection
from integration import (
    run_dispatch_validation,
    calculate_vehicle_operational_costs,
    get_dashboard_kpis,
    get_analytics_data
)

# --- LOGIN GATEKEEPER ---
@current_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Hardcoded credentials for Hackathon presentation
        if request.form['username'] == 'manager' and request.form['password'] == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('dashboard_overview'))
        flash('Invalid Credentials - Access Denied', 'error')
    return render_template('login.html')

@current_app.before_request
def restrict_access():
    allowed_routes = ['login', 'static']
    if not session.get('logged_in') and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# --- PHASE 5: DASHBOARD ---
@current_app.route('/')
def dashboard_overview():
    db_path = current_app.config['DATABASE']
    kpis = get_dashboard_kpis(db_path)
    return render_template('dashboard.html', kpis=kpis, active_page='dashboard')

# --- PHASE 2: REGISTRIES ---
@current_app.route('/vehicles', methods=['GET'])
def list_vehicles():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    conn.close()
    return render_template('vehicles.html', vehicles=vehicles, active_page='vehicles')

@current_app.route('/vehicles/create', methods=['POST'])
def create_vehicle():
    db_path = current_app.config['DATABASE']
    reg_num = request.form['reg_num'].strip().upper()
    model = request.form['model'].strip()
    v_type = request.form['type']
    max_capacity = float(request.form['max_capacity'])
    odometer = float(request.form['odometer'])
    acquisition_cost = float(request.form['acquisition_cost'])
    conn = get_db_connection(db_path)
    try:
        conn.execute('INSERT INTO vehicles (reg_num, model, type, max_capacity, odometer, acquisition_cost, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (reg_num, model, v_type, max_capacity, odometer, acquisition_cost, 'Available'))
        conn.commit()
        flash('Vehicle asset initialized.', 'success')
    finally:
        conn.close()
    return redirect(url_for('list_vehicles'))

@current_app.route('/drivers', methods=['GET'])
def list_drivers():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    drivers = conn.execute('SELECT * FROM drivers').fetchall()
    conn.close()
    return render_template('drivers.html', drivers=drivers, active_page='drivers')

# --- PHASE 3: DISPATCH ---
@current_app.route('/dispatch', methods=['GET'])
def dispatch_dashboard():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles WHERE status = 'Available'").fetchall()
    drivers = conn.execute("SELECT * FROM drivers WHERE status = 'Available'").fetchall()
    conn.close()
    return render_template('dispatcher.html', vehicles=vehicles, drivers=drivers, active_page='dispatch')

@current_app.route('/dispatch/create', methods=['POST'])
def execute_dispatch_transaction():
    db_path = current_app.config['DATABASE']
    is_valid, message = run_dispatch_validation(db_path, request.form['vehicle_ref'], int(request.form['driver_ref']), float(request.form['cargo_weight']))
    if not is_valid:
        flash(f'Deployment Denied: {message}', 'error')
        return redirect(url_for('dispatch_dashboard'))
    conn = get_db_connection(db_path)
    conn.execute('UPDATE vehicles SET status = ? WHERE reg_num = ?', ('On Trip', request.form['vehicle_ref']))
    conn.execute('UPDATE drivers SET status = ? WHERE id = ?', ('On Trip', request.form['driver_ref']))
    conn.execute('INSERT INTO trips (source, destination, vehicle_ref, driver_ref, cargo_weight, planned_distance, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (request.form['source'], request.form['destination'], request.form['vehicle_ref'], request.form['driver_ref'], request.form['cargo_weight'], request.form['planned_distance'], 'Dispatched'))
    conn.commit()
    conn.close()
    return redirect(url_for('dispatch_dashboard'))

# --- PHASE 4: MAINTENANCE & EXPENSES ---
@current_app.route('/maintenance', methods=['GET'])
def maintenance_dashboard():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    logs = conn.execute("SELECT * FROM maintenance_logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('maintenance.html', vehicles=vehicles, logs=logs, active_page='maintenance')

@current_app.route('/maintenance/create', methods=['POST'])
def create_maintenance_log():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    conn.execute('INSERT INTO maintenance_logs (vehicle_ref, title, cost, log_date, status) VALUES (?, ?, ?, ?, ?)',
                 (request.form['vehicle_ref'], request.form['title'], request.form['cost'], request.form['log_date'], 'Open'))
    conn.execute("UPDATE vehicles SET status = 'In Shop' WHERE reg_num = ?", (request.form['vehicle_ref'],))
    conn.commit()
    conn.close()
    return redirect(url_for('maintenance_dashboard'))

@current_app.route('/expenses', methods=['GET'])
def expenses_dashboard():
    db_path = current_app.config['DATABASE']
    vehicles = get_db_connection(db_path).execute("SELECT * FROM vehicles").fetchall()
    summaries = calculate_vehicle_operational_costs(db_path)
    return render_template('expenses.html', vehicles=vehicles, summaries=summaries, active_page='expenses')

# --- PHASE 5: ANALYTICS ---
@current_app.route('/analytics', methods=['GET'])
def analytics_dashboard():
    analytics = get_analytics_data(current_app.config['DATABASE'])
    return render_template('analytics.html', analytics=analytics, active_page='analytics')

@current_app.route('/export/csv', methods=['GET'])
def export_csv():
    analytics = get_analytics_data(current_app.config['DATABASE'])
    def generate():
        yield 'Registration Number,Efficiency,Cost,ROI\n'
        for row in analytics:
            yield f"{row['reg_num']},{row['efficiency']},{row['operational_cost']},{row['roi']}\n"
    return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=transitops_analytics.csv'})