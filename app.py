from flask import Flask, request, jsonify, render_template
import sqlite3
import pyotp
import crypto_manager
import jwt 
import datetime
from functools import wraps

app = Flask(__name__)

# CONFIGURATION
# In a real production app, this key would be hidden in an environment variable, not code.
app.config['SECRET_KEY'] = 'super_secret_enterprise_key_change_this_in_prod'

# UTILITY: Database Connection
def get_db_connection():
    conn = sqlite3.connect('vault.db')
    conn.row_factory = sqlite3.Row 
    return conn

# UTILITY: The "Bouncer" (Decorator)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Look for token in headers
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message': 'Token is missing! Authentication required.'}), 401
        
        try:
            # 2. Decode the token (Verification)
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired! Please login again.'}), 401
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# UTILITY: Auth Helper (Password Check Only)
def verify_password_logic(user_id, master_password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    if not user:
        return None
    
    if crypto_manager.verify_master_password(master_password, user['salt'], user['password_hash']):
        return user
    return None

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password_input = data.get('password')
    code_input = data.get('2fa_code')

    # 1. Find User
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # 2. Verify Password (HASH)
    if not crypto_manager.verify_master_password(password_input, user['salt'], user['password_hash']):
        return jsonify({"error": "Invalid Password"}), 401

    # 3. Verify 2FA (TIME)
    totp = pyotp.TOTP(user['two_factor_secret'])
    if not totp.verify(code_input):
        return jsonify({"error": "Invalid 2FA Code"}), 401

    # 4. GENERATE TOKEN (The "Badge")
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({"token": token}), 200

@app.route('/api/add_password', methods=['POST'])
@token_required 
def add_password_entry(current_user_id):
    data = request.json
    master_password = data.get('master_password') 
    
    user = verify_password_logic(current_user_id, master_password)
    if not user:
        return jsonify({"error": "Invalid Master Password"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)
    encrypted_pw = crypto_manager.encrypt_val(encryption_key, data.get('site_password'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO passwords (user_id, site_name, site_username, encrypted_password)
        VALUES (?, ?, ?, ?)
    ''', (current_user_id, data.get('site_name'), data.get('site_username'), encrypted_pw))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password Saved"}), 201

@app.route('/api/get_passwords', methods=['POST'])
@token_required
def get_all_passwords(current_user_id):
    data = request.json
    master_password = data.get('master_password')

    user = verify_password_logic(current_user_id, master_password)
    if not user:
        return jsonify({"error": "Invalid Master Password"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)

    conn = get_db_connection()
    rows = conn.execute('SELECT id, site_name, site_username, encrypted_password FROM passwords WHERE user_id = ?', (current_user_id,)).fetchall()
    conn.close()

    results = []
    for row in rows:
        try:
            decrypted_pw = crypto_manager.decrypt_val(encryption_key, row['encrypted_password'])
            results.append({
                "id": row['id'],
                "site": row['site_name'],
                "username": row['site_username'],
                "password": decrypted_pw
            })
        except Exception:
            # Enterprise Error Handling: Skip bad rows instead of crashing
            print(f"Error decrypting row {row['id']}")

    return jsonify(results), 200

@app.route('/api/delete_password', methods=['DELETE'])
@token_required
def delete_password_entry(current_user_id):
    data = request.json
    password_id = data.get('id')

    conn = get_db_connection()
    conn.execute('DELETE FROM passwords WHERE id = ? AND user_id = ?', (password_id, current_user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)