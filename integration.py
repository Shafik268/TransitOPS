import sqlite3
from database.database import get_db_connection

# ==========================================
# PHASE 3: DISPATCH & TRIP ROUTINES
# ==========================================

def run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight):
    """Validates asset availability, driver compliance, and maximum load capacity rules."""
    conn = get_db_connection(db_path)
    try:
        vehicle = conn.execute("SELECT status, max_capacity FROM vehicles WHERE reg_num = ?", (vehicle_ref,)).fetchone()
        if not vehicle:
            return False, f"Vehicle {vehicle_ref} does not exist in the master registry."
            
        if vehicle['status'] != 'Available':
            return False, f"Vehicle {vehicle_ref} is currently {vehicle['status']} and cannot be dispatched."
            
        if float(cargo_weight) < 0:
            return False, "Safety Violation: Cargo payload weight cannot be a negative value."
            
        if float(cargo_weight) > vehicle['max_capacity']:
            return False, f"Safety Violation: Cargo weight ({cargo_weight} KG) exceeds vehicle maximum capacity ({vehicle['max_capacity']} KG)."
            
        driver = conn.execute("SELECT status, name FROM drivers WHERE id = ?", (driver_ref,)).fetchone()
        if not driver:
            return False, "Assigned operator ID does not exist in the compliance database."
            
        if driver['status'] != 'Available':
            return False, f"Operator {driver['name']} is currently {driver['status']} and cannot be assigned to a new trip."
            
        return True, "All validation rules passed successfully."
    finally:
        conn.close()

def complete_trip_routine(db_path, trip_id):
    """
    Closes a trip, restores driver and vehicle to Available, 
    and automatically increases the vehicle's odometer by the trip distance.
    """
    conn = get_db_connection(db_path)
    try:
        conn.execute('BEGIN TRANSACTION')
        trip = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        if not trip:
            return False, "Trip reference ID not found."
        if trip['status'] == 'Completed':
            return False, "This trip has already been marked as completed."
            
        veh_ref = trip['vehicle_ref']
        drv_ref = trip['driver_ref']
        distance = float(trip['planned_distance'])
        
        # 1. Mark trip completed
        conn.execute("UPDATE trips SET status = 'Completed' WHERE id = ?", (trip_id,))
        # 2. Restore vehicle status and bump odometer
        conn.execute("UPDATE vehicles SET status = 'Available', odometer = odometer + ? WHERE reg_num = ?", (distance, veh_ref))
        # 3. Restore driver status
        conn.execute("UPDATE drivers SET status = 'Available' WHERE id = ?", (drv_ref,))
        
        conn.commit()
        return True, f"Trip #{trip_id} completed! Vehicle {veh_ref} restored to Available and odometer incremented by {distance} km."
    except Exception as e:
        conn.execute('ROLLBACK')
        return False, f"Database failure during trip completion: {str(e)}"
    finally:
        conn.close()

# ==========================================
# PHASE 4: EXPENSES & COST SUMMARIES
# ==========================================

def calculate_vehicle_operational_costs(db_path):
    """Aggregates fuel logs, maintenance bills, and general overhead expenses per vehicle."""
    conn = get_db_connection(db_path)
    try:
        vehicles = conn.execute("SELECT reg_num, model FROM vehicles").fetchall()
        summaries = []
        for v in vehicles:
            reg = v['reg_num']
            
            fuel_row = conn.execute("SELECT SUM(cost) as c FROM fuel_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
            fuel_cost = float(fuel_row['c'] or 0.0)
            
            maint_row = conn.execute("SELECT SUM(cost) as c FROM maintenance_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
            maint_cost = float(maint_row['c'] or 0.0)
            
            gen_row = conn.execute("SELECT SUM(cost) as c FROM expenses WHERE vehicle_ref = ?", (reg,)).fetchone()
            gen_cost = float(gen_row['c'] or 0.0)
            
            total_cost = round(fuel_cost + maint_cost + gen_cost, 2)
            
            summaries.append({
                'reg_num': reg,
                'model': v['model'],
                'fuel_cost': fuel_cost,
                'maint_cost': maint_cost,
                'gen_cost': gen_cost,
                'total_cost': total_cost
            })
        return summaries
    finally:
        conn.close()

# ==========================================
# PHASE 5: LIVE DASHBOARD KPI ENGINE
# ==========================================

def get_dashboard_kpis(db_path):
    """Calculates real-time KPIs for the main dashboard layout, capping utilization at 100%."""
    conn = get_db_connection(db_path)
    try:
        total_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles").fetchone()['c'] or 0
        avail_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='Available'").fetchone()['c'] or 0
        active_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='On Trip'").fetchone()['c'] or 0
        maint_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='In Shop'").fetchone()['c'] or 0
        
        active_trips = conn.execute("SELECT COUNT(*) as c FROM trips WHERE status='Dispatched'").fetchone()['c'] or 0
        drivers_duty = conn.execute("SELECT COUNT(*) as c FROM drivers WHERE status='On Trip'").fetchone()['c'] or 0
        
        # Calculate percentage and clamp between 0.0 and 100.0
        raw_util = (active_veh / total_veh * 100.0) if total_veh > 0 else 0.0
        utilization = round(max(0.0, min(100.0, raw_util)), 1)
        
        return {
            'total_vehicles': total_veh,
            'active_vehicles': active_veh,
            'available_vehicles': avail_veh,
            'maintenance_vehicles': maint_veh,
            'active_trips': active_trips,
            'drivers_duty': drivers_duty,
            'utilization': utilization
        }
    finally:
        conn.close()

# ==========================================
# PHASE 5: ANALYTICS & ROI MATH ENGINE
# ==========================================

def get_analytics_data(db_path):
    """
    Computes Fuel Efficiency (KM/L) and Vehicle ROI metrics safely.
    Subtracts ALL operational costs (fuel + maintenance + general expenses) from revenue.
    """
    conn = get_db_connection(db_path)
    try:
        vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
        analytics = []
        for v in vehicles:
            reg = v['reg_num']
            acq_cost = float(v['acquisition_cost'] or 0.0)
            
            fuel_row = conn.execute("SELECT SUM(liters) as l, SUM(cost) as c FROM fuel_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
            fuel_liters = float(fuel_row['l'] or 0.0)
            fuel_cost = float(fuel_row['c'] or 0.0)
            
            dist_row = conn.execute("SELECT SUM(planned_distance) as d FROM trips WHERE vehicle_ref = ?", (reg,)).fetchone()
            distance = float(dist_row['d'] or 0.0)
            
            maint_row = conn.execute("SELECT SUM(cost) as c FROM maintenance_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
            maint_cost = float(maint_row['c'] or 0.0)

            gen_row = conn.execute("SELECT SUM(cost) as c FROM expenses WHERE vehicle_ref = ?", (reg,)).fetchone()
            gen_cost = float(gen_row['c'] or 0.0)
            
            # Zero-division safe efficiency formula
            efficiency = round(distance / fuel_liters, 2) if fuel_liters > 0 else 0.0
            
            # Mocking Revenue: Standard freight rate of 50 INR per KM traveled
            revenue = distance * 50.0
            total_overhead = fuel_cost + maint_cost + gen_cost
            
            # Zero-division safe ROI formula accounting for all overhead
            roi = round(((revenue - total_overhead) / acq_cost) * 100.0, 2) if acq_cost > 0 else 0.0
            
            analytics.append({
                'reg_num': reg,
                'efficiency': efficiency,
                'operational_cost': round(total_overhead, 2),
                'roi': roi
            })
        return analytics
    finally:
        conn.close()