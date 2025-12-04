from flask import Flask, request, jsonify
import sqlite3
import pyotp
import crypto_manager

app = Flask(__name__)

# UTILITY: Database Connection
def get_db_connection():
    conn = sqlite3.connect('vault.db')
    # This allows us to access columns by name (row['username']) instead of number (row[0])
    conn.row_factory = sqlite3.Row 
    return conn

# --- ENDPOINTS ---

@app.route('/api/login', methods=['POST'])
def login():
    # 1. Receive data from the "Client" (JSON format)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    username = data.get('username')
    password_input = data.get('password')
    code_input = data.get('2fa_code')

    # 2. Find the user in the database
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user is None:
        return jsonify({"error": "User not found"}), 404

    # 3. Verify the Master Password (HASH CHECK)
    # We grab the salt and hash from the DB to compare against input
    stored_salt = user['salt']
    stored_hash = user['password_hash']
    
    is_password_correct = crypto_manager.verify_master_password(
        password_input, 
        stored_salt, 
        stored_hash
    )

    if not is_password_correct:
        return jsonify({"error": "Invalid Password"}), 401

    # 4. Verify 2FA (TIME CHECK)
    # We retrieve the secret we saved earlier
    secret = user['two_factor_secret']
    totp = pyotp.TOTP(secret)
    
    # We ask pyotp: "Is this code valid right now?"
    if totp.verify(code_input):
        return jsonify({"message": "LOGIN SUCCESSFUL! Vault Unlocked."}), 200
    else:
        return jsonify({"error": "Invalid 2FA Code"}), 401

# Run the server
if __name__ == '__main__':
    # port=5000 is standard for Flask
    app.run(debug=True, port=5000)