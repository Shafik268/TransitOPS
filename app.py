import os
from flask import Flask
from database.database import init_db

app = Flask(__name__)
# Secure token for session management
app.secret_key = 'velocityone_super_secret_key_2026'

# Enforce isolated directory validation paths
DATABASE = os.path.join(app.root_path, 'database', 'transitops.db')
app.config['DATABASE'] = DATABASE

# Force table initialization on application boot
with app.app_context():
    init_db(app.config['DATABASE'])
    import routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)