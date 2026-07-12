import os
from flask import Flask, render_template
from database.database import init_db

app = Flask(__name__)
app.secret_key = 'transitops_hackathon_super_secret_token_key'

# Directory validation paths
DATABASE = os.path.join(app.root_path, 'database', 'transitops.db')

# Connection hook parameters inside app
app.config['DATABASE'] = DATABASE

@app.before_request
def setup_environment():
    """Guarantee database components are systematically mapped prior to traffic handling."""
    if not os.path.exists(app.config['DATABASE']):
        init_db(app.config['DATABASE'])

# Import core routes after app instantiation context to prevent slips
with app.app_context():
    import routes

if __name__ == '__main__':
    # Initialize framework execution loop
    app.run(host='0.0.0.0', port=5000, debug=True)