import sqlite3
from datetime import datetime

def check_driver_validity(driver_row):
    """Enforce security validation procedures assessing operational suitability constraints[cite: 3].
    
    Returns tuple: (bool, description_string)
    """
    
    if driver_row['status'] == 'Suspended':
        return False, "Driver Operative carries an active system suspension status flag[cite: 3]."
    
    if driver_row['status'] == 'Off Duty':
        return False, "Operator is currently registered as Off Duty[cite: 3]."
        
    
    try:
        expiry = datetime.strptime(driver_row['expiry_date'], '%Y-%m-%d')
        if expiry.date() < datetime.now().date():
            return False, "Driver qualification validation rejected: Driving license parameters have expired[cite: 3]."
    except ValueError:
        return False, "Malformed context date configuration logs found in profile index."
        
    return True, "Operational authorization verified."

def check_vehicle_dispatch_availability(vehicle_row):
    """Scan machine parameters against exclusion matrices prior to routing actions[cite: 3]."""
    forbidden_states = ['In Shop', 'Retired']
    if vehicle_row['status'] in forbidden_states:
        return False, f"Asset is unavailable for routing workflows due to: '{vehicle_row['status']}' state tracking[cite: 3]."
    return True, "Asset tracking parameter matches deployment availability metrics."

from database.database import get_db_connection
from datetime import datetime

def run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight):
    """Enforce complete cross-checks prior to commitment routines[cite: 3].
    
    Returns tuple: (bool, error_message_string)
    """
    conn = get_db_connection(db_path)
    
    vehicle = conn.execute('SELECT * FROM vehicles WHERE reg_num = ?', (vehicle_ref,)).fetchone()
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_ref,)).fetchone()
    
    conn.close()
    
    if not vehicle:
        return False, "Target deployment vehicle identifier could not be verified."
    if not driver:
        return False, "Assigned operator identity reference is missing from directories."
        
    
    if cargo_weight > vehicle['max_capacity']:
        return False, f"Cargo weight ({cargo_weight} KG) breaks max payload bounds ({vehicle['max_capacity']} KG)[cite: 3]."
        
    
    if vehicle['status'] != 'Available':
        return False, f"Selected asset is disqualified due to active status flag: '{vehicle['status']}'[cite: 3]."
        
    if driver['status'] != 'Available':
        return False, f"Assigned driver operator is non-eligible due to current status: '{driver['status']}'[cite: 3]."
        
    
    if driver['status'] == 'Suspended':
        return False, "Operative is flagged as Suspended across company records[cite: 3]."
        
    try:
        expiry_date = datetime.strptime(driver['expiry_date'], '%Y-%m-%d').date()
        if expiry_date < datetime.now().date():
            return False, f"Operator licensing expiration threshold breached on date: {driver['expiry_date']}[cite: 3]."
    except ValueError:
        return False, "Internal validation engine failed to parse operator date signature format."

    return True, "All validation checkpoints passed successfully."