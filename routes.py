import sqlite3
from flask import current_app, render_template, request, redirect, url_for, flash, Response, session
from database.database import get_db_connection
from integration import (
    run_dispatch_validation,
    calculate_vehicle_operational_costs,
    get_dashboard_kpis,
    get_analytics_data
)

# ==========================================
# GATEKEEPER: AUTO-SIGNUP & LOGIN ENGINE
# ==========================================

@current_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        db_path = current_app.config['DATABASE']
        conn = get_db_connection(db_path)
        
        user = conn.execute("SELECT * FROM managers WHERE username = ?", (username,)).fetchone()
        
        if user:
            if user['password'] == password:
                session['logged_in'] = True
                session['username'] = username
                conn.close()
                return redirect(url_for('dashboard_overview'))
            else:
                flash('Incorrect password for existing account.', 'error')
        else:
            try:
                conn.execute("INSERT INTO managers (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                session['logged_in'] = True
                session['username'] = username
                flash('New account registered and authenticated! Welcome to VelocityOne.', 'success')
                conn.close()
                return redirect(url_for('dashboard_overview'))
            except Exception as e:
                flash(f'Registration error: {str(e)}', 'error')
        
        conn.close()
    return render_template('login.html')

@current_app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out securely.', 'success')
    return redirect(url_for('login'))

@current_app.before_request
def restrict_access():
    allowed_routes = ['login', 'static']
    if not session.get('logged_in') and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# ==========================================
# PHASE 5: MAIN DASHBOARD ROUTING
# ==========================================

@current_app.route('/')
def dashboard_overview():
    db_path = current_app.config['DATABASE']
    kpis = get_dashboard_kpis(db_path)
    return render_template('dashboard.html', kpis=kpis, active_page='dashboard')

# ==========================================
# PHASE 2: VEHICLES & DRIVERS REGISTRIES
# ==========================================

@current_app.route('/vehicles', methods=['GET'])
def list_vehicles():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    conn.close()
    return render_template('vehicles.html', vehicles=vehicles, active_page='vehicles')

# Aliases to prevent 404 errors on vehicle submission
@current_app.route('/vehicles/create', methods=['POST'])
@current_app.route('/vehicle/create', methods=['POST'])
@current_app.route('/vehicle/add', methods=['POST'])
@current_app.route('/vehicles/add', methods=['POST'])
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
        conn.execute(
            'INSERT INTO vehicles (reg_num, model, type, max_capacity, odometer, acquisition_cost, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (reg_num, model, v_type, max_capacity, odometer, acquisition_cost, 'Available')
        )
        conn.commit()
        flash('Vehicle asset initialized successfully into VelocityOne registry.', 'success')
    except sqlite3.IntegrityError:
        flash(f'Validation Rejection: Asset Registration Identifier "{reg_num}" matches an existing file inside the registry.', 'error')
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

# Aliases to prevent 404 errors on driver submission (Fixes video error at 00:16)
@current_app.route('/drivers/create', methods=['POST'])
@current_app.route('/driver/create', methods=['POST'])
@current_app.route('/driver/add', methods=['POST'])
@current_app.route('/drivers/add', methods=['POST'])
def create_driver():
    db_path = current_app.config['DATABASE']
    name = request.form['name'].strip()
    license_num = request.form['license_num'].strip().upper()
    license_cat = request.form['license_cat'].strip().upper()
    expiry_date = request.form['expiry_date']
    contact = request.form['contact'].strip()
    safety_score = float(request.form['safety_score'])
    
    conn = get_db_connection(db_path)
    try:
        conn.execute(
            'INSERT INTO drivers (name, license_num, license_cat, expiry_date, contact, safety_score, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, license_num, license_cat, expiry_date, contact, safety_score, 'Available')
        )
        conn.commit()
        flash('Driver profile compiled and authenticated within global organizational safety logs.', 'success')
    except sqlite3.IntegrityError:
        flash(f'Validation Rejection: License Identifier Number "{license_num}" already cataloged.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('list_drivers'))

# ==========================================
# PHASE 3: TRIP DISPATCHER ENGINE
# ==========================================

@current_app.route('/dispatch', methods=['GET'])
def dispatch_dashboard():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    
    vehicles = conn.execute("SELECT * FROM vehicles WHERE status = 'Available'").fetchall()
    drivers = conn.execute("SELECT * FROM drivers WHERE status = 'Available'").fetchall()
    conn.close()
    
    return render_template('dispatcher.html', vehicles=vehicles, drivers=drivers, active_page='dispatch')

# Aliases to prevent 404 errors on trip dispatch
@current_app.route('/dispatch/create', methods=['POST'])
@current_app.route('/dispatch/add', methods=['POST'])
@current_app.route('/trip/create', methods=['POST'])
@current_app.route('/trips/create', methods=['POST'])
def execute_dispatch_transaction():
    db_path = current_app.config['DATABASE']
    
    source = request.form['source'].strip()
    destination = request.form['destination'].strip()
    vehicle_ref = request.form['vehicle_ref'].strip()
    driver_ref = int(request.form['driver_ref'])
    cargo_weight = float(request.form['cargo_weight'])
    planned_distance = float(request.form['planned_distance'])
    
    is_valid, message = run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight)
    
    if not is_valid:
        flash(f'Deployment Denied: {message}', 'error')
        return redirect(url_for('dispatch_dashboard'))
        
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        conn.execute(
            'INSERT INTO trips (source, destination, vehicle_ref, driver_ref, cargo_weight, planned_distance, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (source, destination, vehicle_ref, driver_ref, cargo_weight, planned_distance, 'Dispatched')
        )
        conn.execute("UPDATE vehicles SET status = 'On Trip' WHERE reg_num = ?", (vehicle_ref,))
        conn.execute("UPDATE drivers SET status = 'On Trip' WHERE id = ?", (driver_ref,))
        conn.commit()
        flash(f'Authorization Confirmed: Trip successfully dispatched. Vehicle {vehicle_ref} and Operator assigned.', 'success')
    except Exception as e:
        conn.execute('ROLLBACK')
        flash(f'Critical Engine Fault: Database routine collapsed. Traces: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('dispatch_dashboard'))

# ==========================================
# PHASE 4: MAINTENANCE ROUTING ENDPOINTS
# ==========================================

@current_app.route('/maintenance', methods=['GET'])
def maintenance_dashboard():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    logs = conn.execute("SELECT * FROM maintenance_logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('maintenance.html', vehicles=vehicles, logs=logs, active_page='maintenance')

# Aliases to prevent 404 errors on maintenance log submission
@current_app.route('/maintenance/create', methods=['POST'])
@current_app.route('/maintenance/add', methods=['POST'])
@current_app.route('/log/create', methods=['POST'])
def create_maintenance_log():
    db_path = current_app.config['DATABASE']
    vehicle_ref = request.form['vehicle_ref'].strip()
    title = request.form['title'].strip()
    cost = float(request.form['cost'])
    log_date = request.form['log_date']
    notes = request.form.get('notes', '').strip() if 'notes' in request.form else ''
    
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        conn.execute(
            'INSERT INTO maintenance_logs (vehicle_ref, title, cost, log_date, status, notes) VALUES (?, ?, ?, ?, ?, ?)',
            (vehicle_ref, title, cost, log_date, 'Open', notes)
        )
        conn.execute("UPDATE vehicles SET status = 'In Shop' WHERE reg_num = ?", (vehicle_ref,))
        conn.commit()
        flash(f'Service logged for {vehicle_ref}. Vehicle status automatically switched to In Shop.', 'warning')
    except Exception as e:
        conn.execute('ROLLBACK')
        flash(f'Error logging maintenance: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('maintenance_dashboard'))

@current_app.route('/maintenance/close/<int:log_id>', methods=['POST', 'GET'])
def close_maintenance_log(log_id):
    db_path = current_app.config['DATABASE']
    vehicle_ref = request.form.get('vehicle_ref')
    
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        if not vehicle_ref:
            log_entry = conn.execute("SELECT vehicle_ref FROM maintenance_logs WHERE id = ?", (log_id,)).fetchone()
            if log_entry:
                vehicle_ref = log_entry['vehicle_ref']
                
        conn.execute("UPDATE maintenance_logs SET status = 'Closed' WHERE id = ?", (log_id,))
        if vehicle_ref:
            conn.execute("UPDATE vehicles SET status = 'Available' WHERE reg_num = ?", (vehicle_ref,))
        conn.commit()
        flash(f'Maintenance closed for {vehicle_ref}. Vehicle restored to Available status.', 'success')
    except Exception as e:
        conn.execute('ROLLBACK')
        flash(f'Error closing maintenance: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('maintenance_dashboard'))

# ==========================================
# PHASE 4: FUEL & EXPENSES ENDPOINTS
# ==========================================

@current_app.route('/expenses', methods=['GET'])
def expenses_dashboard():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    conn.close()
    
    summaries = calculate_vehicle_operational_costs(db_path)
    return render_template('expenses.html', vehicles=vehicles, summaries=summaries, active_page='expenses')

# Aliases to prevent 404 errors on fuel intake submission (Fixes video error at 01:10)
@current_app.route('/expenses/fuel/create', methods=['POST'])
@current_app.route('/fuel/create', methods=['POST'])
@current_app.route('/fuel/add', methods=['POST'])
@current_app.route('/expenses/fuel/add', methods=['POST'])
def create_fuel_log():
    db_path = current_app.config['DATABASE']
    vehicle_ref = request.form['vehicle_ref'].strip()
    liters = float(request.form['liters'])
    cost = float(request.form['cost'])
    log_date = request.form['log_date']
    
    conn = get_db_connection(db_path)
    conn.execute(
        'INSERT INTO fuel_logs (vehicle_ref, liters, cost, log_date) VALUES (?, ?, ?, ?)',
        (vehicle_ref, liters, cost, log_date)
    )
    conn.commit()
    conn.close()
    flash(f'Fuel log recorded successfully for {vehicle_ref}.', 'success')
    return redirect(url_for('expenses_dashboard'))

# Aliases to prevent 404 errors on general expense submission (Fixes video error at 01:23)
@current_app.route('/expenses/general/create', methods=['POST'])
@current_app.route('/expense/create', methods=['POST'])
@current_app.route('/expense/add', methods=['POST'])
@current_app.route('/expenses/create', methods=['POST'])
@current_app.route('/expenses/add', methods=['POST'])
@current_app.route('/expenses/general/add', methods=['POST'])
def create_general_expense():
    db_path = current_app.config['DATABASE']
    vehicle_ref = request.form['vehicle_ref'].strip()
    expense_type = request.form['expense_type']
    cost = float(request.form['cost'])
    log_date = request.form['log_date']
    
    conn = get_db_connection(db_path)
    conn.execute(
        'INSERT INTO expenses (vehicle_ref, expense_type, cost, log_date) VALUES (?, ?, ?, ?)',
        (vehicle_ref, expense_type, cost, log_date)
    )
    conn.commit()
    conn.close()
    flash(f'{expense_type} expense recorded successfully for {vehicle_ref}.', 'success')
    return redirect(url_for('expenses_dashboard'))

# ==========================================
# PHASE 5: ANALYTICS & CSV REPORTING
# ==========================================

@current_app.route('/analytics', methods=['GET'])
def analytics_dashboard():
    db_path = current_app.config['DATABASE']
    analytics = get_analytics_data(db_path)
    return render_template('analytics.html', analytics=analytics, active_page='analytics')

@current_app.route('/export/csv', methods=['GET'])
def export_csv():
    db_path = current_app.config['DATABASE']
    analytics = get_analytics_data(db_path)
    
    def generate_csv():
        yield 'Registration Number,Fuel Efficiency (KM/L),Total Operational Cost (INR),Vehicle ROI (%)\n'
        for row in analytics:
            yield f"{row['reg_num']},{row['efficiency']},{row['operational_cost']},{row['roi']}\n"
            
    return Response(
        generate_csv(), 
        mimetype='text/csv', 
        headers={'Content-Disposition': 'attachment; filename=velocityone_analytics.csv'}
    )