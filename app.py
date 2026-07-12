import os
from flask import Flask
from database.database import init_db

app = Flask(__name__)
app.secret_key = 'transitops_hackathon_super_secret_token_key'

# Enforce explicit isolated directory validation paths
DATABASE = os.path.join(app.root_path, 'database', 'transitops.db')
app.config['DATABASE'] = DATABASE

# FORCE INITIALIZE TABLES ON BOOT: 
# This guarantees that even if an empty .db file exists, the tables get built immediately!
with app.app_context():
    init_db(app.config['DATABASE'])
    # Import routes inside app_context so they bind to app cleanly without duplication
    import routes

if __name__ == '__main__':
    # Initialize framework execution loop on default port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)