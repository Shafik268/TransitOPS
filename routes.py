from flask import current_app, render_template

@current_app.route('/')
def dashboard_overview():
    """Primary layout routing tracking current transactional metrics."""
    return render_template('base.html', active_page='dashboard')

from flask import current_app, render_template, request, redirect, url_for, flash
import sqlite3
from database.database import get_db_connection

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
    """Deliver complete operational directory containing all operator files and scores[cite: 3]."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    drivers = conn.execute('SELECT * FROM drivers').fetchall()
    conn.close()
    return render_template('drivers.html', drivers=drivers, active_page='drivers')

@current_app.route('/drivers/create', methods=['POST'])
def create_driver():
    """Ingest explicit driver operational records into localized verification ledgers[cite: 3]."""
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

from flask import current_app, render_template, request, redirect, url_for, flash
from database.database import get_db_connection
from integration import run_dispatch_validation

@current_app.route('/dispatch', methods=['GET'])
def dispatch_dashboard():
    """Deliver configuration form arrays containing only eligible asset elements."""
    db_path = current_app.config['DATABASE']
    conn = get_db_connection(db_path)
    
    # Structural rule: Fetch only available assets for matching
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
    
    # Delegate logic execution down to Arnob's framework 
    is_valid, message = run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight)
    
    if not is_valid:
        flash(f'Deployment Denied: {message}', 'error')
        return redirect(url_for('dispatch_dashboard'))
        
    conn = get_db_connection(db_path)
    try:
        # Open transaction scope block
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