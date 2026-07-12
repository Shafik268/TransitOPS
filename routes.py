from flask import current_app, render_template

@current_app.route('/')
def dashboard_overview():
    """Primary layout routing tracking current transactional metrics."""
    return render_template('base.html', active_page='dashboard')