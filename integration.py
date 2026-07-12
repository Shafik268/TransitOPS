import sqlite3
from datetime import datetime

def check_driver_validity(driver_row):
    """Enforce security validation procedures assessing operational suitability constraints[cite: 3].
    
    Returns tuple: (bool, description_string)
    """
    # Rule 1: Evaluate explicit status boundaries[cite: 3]
    if driver_row['status'] == 'Suspended':
        return False, "Driver Operative carries an active system suspension status flag[cite: 3]."
    
    if driver_row['status'] == 'Off Duty':
        return False, "Operator is currently registered as Off Duty[cite: 3]."
        
    # Rule 2: Evaluate calendar expiration thresholds[cite: 3]
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