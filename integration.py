import sqlite3
from database.database import get_db_connection

# ==========================================
# PHASE 3: DISPATCH VALIDATION ENGINE
# ==========================================

def run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight):
    """
    Acts as the operational gatekeeper before any trip is dispatched.
    Validates asset availability and enforces max load capacity rules.
    """
    conn = get_db_connection(db_path)
    
    # 1. Fetch Vehicle Status and Capacity
    vehicle = conn.execute(
        "SELECT status, max_capacity FROM vehicles WHERE reg_num = ?", 
        (vehicle_ref,)
    ).fetchone()
    
    if not vehicle:
        conn.close()
        return False, f"Vehicle {vehicle_ref} does not exist in the master registry."
        
    if vehicle['status'] != 'Available':
        conn.close()
        return False, f"Vehicle {vehicle_ref} is currently {vehicle['status']} and cannot be dispatched."
        
    # 2. Enforce Load Capacity Rule
    if cargo_weight > vehicle['max_capacity']:
        conn.close()
        return False, f"Safety Violation: Cargo weight ({cargo_weight} KG) exceeds vehicle maximum capacity ({vehicle['max_capacity']} KG)."
        
    # 3. Fetch Driver Status
    driver = conn.execute(
        "SELECT status, name FROM drivers WHERE id = ?", 
        (driver_ref,)
    ).fetchone()
    
    if not driver:
        conn.close()
        return False, "Assigned operator ID does not exist in the compliance database."
        
    if driver['status'] != 'Available':
        conn.close()
        return False, f"Operator {driver['name']} is currently {driver['status']} and cannot be assigned to a new trip."
        
    conn.close()
    return True, "All validation rules passed successfully."

# ==========================================
# PHASE 4: EXPENSES & COST SUMMARIES
# ==========================================

def calculate_vehicle_operational_costs(db_path):
    """
    Aggregates fuel logs, maintenance bills, and general overhead expenses per vehicle.
    """
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT reg_num, model FROM vehicles").fetchall()
    
    summaries = []
    for v in vehicles:
        reg = v['reg_num']
        
        # Total Fuel Cost
        fuel_row = conn.execute("SELECT SUM(cost) as c FROM fuel_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        fuel_cost = fuel_row['c'] or 0.0
        
        # Total Maintenance Cost
        maint_row = conn.execute("SELECT SUM(cost) as c FROM maintenance_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        maint_cost = maint_row['c'] or 0.0
        
        # Total General Expenses
        gen_row = conn.execute("SELECT SUM(cost) as c FROM expenses WHERE vehicle_ref = ?", (reg,)).fetchone()
        gen_cost = gen_row['c'] or 0.0
        
        total_cost = round(fuel_cost + maint_cost + gen_cost, 2)
        
        summaries.append({
            'reg_num': reg,
            'model': v['model'],
            'fuel_cost': fuel_cost,
            'maint_cost': maint_cost,
            'gen_cost': gen_cost,
            'total_cost': total_cost
        })
        
    conn.close()
    return summaries

# ==========================================
# PHASE 5: LIVE DASHBOARD KPI ENGINE
# ==========================================

def get_dashboard_kpis(db_path):
    """
    Calculates real-time KPIs for the main dashboard layout.
    Includes Total Vehicles and fixes the Active Vehicles status check.
    """
    conn = get_db_connection(db_path)
    
    total_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles").fetchone()['c']
    avail_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='Available'").fetchone()['c']
    
    # Counts vehicles currently on trip
    active_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='On Trip'").fetchone()['c']
    maint_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='In Shop'").fetchone()['c']
    
    active_trips = conn.execute("SELECT COUNT(*) as c FROM trips WHERE status='Dispatched'").fetchone()['c']
    drivers_duty = conn.execute("SELECT COUNT(*) as c FROM drivers WHERE status='On Trip'").fetchone()['c']
    
    # Fleet Utilization = (Active Vehicles / Total Vehicles) * 100
    utilization = round((active_veh / total_veh * 100) if total_veh > 0 else 0.0, 1)
    
    conn.close()
    return {
        'total_vehicles': total_veh,
        'active_vehicles': active_veh,
        'available_vehicles': avail_veh,
        'maintenance_vehicles': maint_veh,
        'active_trips': active_trips,
        'drivers_duty': drivers_duty,
        'utilization': utilization
    }

# ==========================================
# PHASE 5: ANALYTICS & ROI MATH ENGINE
# ==========================================

def get_analytics_data(db_path):
    """
    Computes Fuel Efficiency (KM/L) and Vehicle ROI metrics based on exact formulas.
    """
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    
    analytics = []
    for v in vehicles:
        reg = v['reg_num']
        acq_cost = v['acquisition_cost']
        
        # Fuel consumed and cost
        fuel_row = conn.execute("SELECT SUM(liters) as l, SUM(cost) as c FROM fuel_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        fuel_liters = fuel_row['l'] or 0.0
        fuel_cost = fuel_row['c'] or 0.0
        
        # Distance traveled (Total planned distance of all dispatched trips)
        dist_row = conn.execute("SELECT SUM(planned_distance) as d FROM trips WHERE vehicle_ref = ?", (reg,)).fetchone()
        distance = dist_row['d'] or 0.0
        
        # Maintenance Costs
        maint_row = conn.execute("SELECT SUM(cost) as c FROM maintenance_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        maint_cost = maint_row['c'] or 0.0
        
        # Formula 1: Fuel Efficiency = Distance / Fuel Consumed
        efficiency = round(distance / fuel_liters, 2) if fuel_liters > 0 else 0.0
        
        # Mocking Revenue for ROI: Standard freight rate of 50 INR per KM traveled
        revenue = distance * 50.0
        
        # Formula 2: ROI = ((Revenue - (Maintenance + Fuel)) / Acquisition Cost) * 100
        roi = round(((revenue - (maint_cost + fuel_cost)) / acq_cost) * 100, 2) if acq_cost > 0 else 0.0
        
        analytics.append({
            'reg_num': reg,
            'efficiency': efficiency,
            'operational_cost': fuel_cost + maint_cost,
            'roi': roi
        })
        
    conn.close()
    return analytics