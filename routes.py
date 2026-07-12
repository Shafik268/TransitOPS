import sqlite3
from flask import current_app, render_template, request, redirect, url_for, flash, Response
from database.database import get_db_connection
from integration import (
    run_dispatch_validation,
    calculate_vehicle_operational_costs,
    get_dashboard_kpis,
    get_analytics_data
)

# ==========================================
# PHASE 5: MAIN DASHBOARD ROUTING
# ==========================================

@current_app.route('/')
def dashboard_overview():
    """Primary layout routing tracking current transactional KPI metrics."""
    db_path = current_app.config['DATABASE']
    kpis = get_dashboard_kpis(db_path)
    return render_template('dashboard.html', kpis=kpis, active_page='dashboard')

# ==========================================
# PHASE 2: VEHICLES & DRIVERS REGISTRIES
# ==========================================

@current_app.route('/vehicles', methods=['GET'])
def list_vehicles():
    """Retrieve all current machine asset configurations registered across storage engines."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    conn.close()
    return render_template('vehicles.html', vehicles=vehicles, active_page='vehicles')

@current_app.route('/vehicles/create', methods=['POST'])
def create_vehicle():
    """Ingest asset creation parameters, validating item identity uniqueness fields."""
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
        flash('Vehicle asset initialized successfully into centralized network repository.', 'success')
    except sqlite3.IntegrityError:
        flash(f'Validation Rejection: Asset Registration Identifier "{reg_num}" matches an existing file inside the registry.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('list_vehicles'))

@current_app.route('/drivers', methods=['GET'])
def list_drivers():
    """Deliver complete operational directory containing all operator files and scores."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    drivers = conn.execute('SELECT * FROM drivers').fetchall()
    conn.close()
    return render_template('drivers.html', drivers=drivers, active_page='drivers')

@current_app.route('/drivers/create', methods=['POST'])
def create_driver():
    """Ingest explicit driver operational records into localized verification ledgers."""
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
    """Deliver configuration form arrays containing only eligible asset elements."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    
    vehicles = conn.execute("SELECT * FROM vehicles WHERE status = 'Available'").fetchall()
    drivers = conn.execute("SELECT * FROM drivers WHERE status = 'Available'").fetchall()
    conn.close()
    
    return render_template('dispatcher.html', vehicles=vehicles, drivers=drivers, active_page='dispatch')

@current_app.route('/dispatch/create', methods=['POST'])
def execute_dispatch_transaction():
    """Process incoming routing transactions through rule integration engines safely."""
    db_path = current_app.config['DATABASE']
    
    source = request.form['source'].strip()
    destination = request.form['destination'].strip()
    vehicle_ref = request.form['vehicle_ref'].strip()
    driver_ref = int(request.form['driver_ref'])
    cargo_weight = float(request.form['cargo_weight'])
    planned_distance = float(request.form['planned_distance'])
    
    # Delegate logic execution down to Arnob's validation framework middleware
    is_valid, message = run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight)
    
    if not is_valid:
        flash(f'Deployment Denied: {message}', 'error')
        return redirect(url_for('dispatch_dashboard'))
        
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        
        # 1. Log deployment entry into trips registry data matrix
        conn.execute(
            'INSERT INTO trips (source, destination, vehicle_ref, driver_ref, cargo_weight, planned_distance, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (source, destination, vehicle_ref, driver_ref, cargo_weight, planned_distance, 'Dispatched')
        )
        
        # 2. Automated Trigger: Flip matching asset parameters status fields to 'On Trip'
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
    """Deliver maintenance service logs and eligible vehicle lists."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    logs = conn.execute("SELECT * FROM maintenance_logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('maintenance.html', vehicles=vehicles, logs=logs, active_page='maintenance')

@current_app.route('/maintenance/create', methods=['POST'])
def create_maintenance_log():
    """Log service entry and automatically transition vehicle status to 'In Shop'."""
    db_path = current_app.config['DATABASE']
    vehicle_ref = request.form['vehicle_ref'].strip()
    title = request.form['title'].strip()
    cost = float(request.form['cost'])
    log_date = request.form['log_date']
    notes = request.form.get('notes', '').strip()
    
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        # 1. Insert maintenance record
        conn.execute(
            'INSERT INTO maintenance_logs (vehicle_ref, title, cost, log_date, status, notes) VALUES (?, ?, ?, ?, ?, ?)',
            (vehicle_ref, title, cost, log_date, 'Open', notes)
        )
        # 2. Automated Business Rule: Switch vehicle status to 'In Shop'
        conn.execute("UPDATE vehicles SET status = 'In Shop' WHERE reg_num = ?", (vehicle_ref,))
        conn.commit()
        flash(f'Service logged for {vehicle_ref}. Vehicle status automatically switched to In Shop.', 'warning')
    except Exception as e:
        conn.execute('ROLLBACK')
        flash(f'Error logging maintenance: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('maintenance_dashboard'))

@current_app.route('/maintenance/close/<int:log_id>', methods=['POST'])
def close_maintenance_log(log_id):
    """Close maintenance log and restore vehicle status back to 'Available'."""
    db_path = current_app.config['DATABASE']
    vehicle_ref = request.form['vehicle_ref'].strip()
    
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        # 1. Mark log as Closed
        conn.execute("UPDATE maintenance_logs SET status = 'Closed' WHERE id = ?", (log_id,))
        # 2. Automated Business Rule: Restore vehicle status to 'Available'
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
    """Deliver fuel/expense ingestion forms and automated cost summary breakdown."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    conn.close()
    
    # Calculate automated per-vehicle summaries using Arnob's logic engine
    summaries = calculate_vehicle_operational_costs(db_path)
    return render_template('expenses.html', vehicles=vehicles, summaries=summaries, active_page='expenses')

@current_app.route('/expenses/fuel/create', methods=['POST'])
def create_fuel_log():
    """Log refueling transaction."""
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

@current_app.route('/expenses/general/create', methods=['POST'])
def create_general_expense():
    """Log general operational overhead expense."""
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
    """Render the ROI and Fuel Efficiency metrics matrix."""
    db_path = current_app.config['DATABASE']
    analytics = get_analytics_data(db_path)
    return render_template('analytics.html', analytics=analytics, active_page='analytics')

@current_app.route('/export/csv', methods=['GET'])
def export_csv():
    """Dynamically generate and download a CSV file of the Analytics metrics."""
    db_path = current_app.config['DATABASE']
    analytics = get_analytics_data(db_path)
    
    def generate_csv():
        # Header row
        yield 'Registration Number,Fuel Efficiency (KM/L),Total Operational Cost (INR),Vehicle ROI (%)\n'
        # Data rows
        for row in analytics:
            yield f"{row['reg_num']},{row['efficiency']},{row['operational_cost']},{row['roi']}\n"
            
    # Return standard CSV headers forcing a browser file download
    return Response(
        generate_csv(), 
        mimetype='text/csv', 
        headers={'Content-Disposition': 'attachment; filename=transitops_analytics.csv'}
    )