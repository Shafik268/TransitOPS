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
        flash('Vehicle asset initialized successfully into centralized network repository.', 'success')
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

@current_app.route('/expenses', methods=['GET'])
def expenses_dashboard():
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    conn.close()
    
    # Calculate automated per-vehicle summaries using Arnob's logic engine
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
            
    # Return standard CSV headers forcing a browser file download
    return Response(
        generate(), 
        mimetype='text/csv', 
        headers={'Content-Disposition': 'attachment; filename=transitops_analytics.csv'}
    )