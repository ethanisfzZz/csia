"""
Simple authentication module for single-user crypto trading bot.
"""

import os
import csv
import hashlib
import secrets
import time
from functools import wraps
from flask import request, jsonify

# Simple session store
active_sessions = {}
SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours

USER_CSV_PATH = "./dataframe/user.csv"

def create_session(username):
    """Create a new session token."""
    token = secrets.token_urlsafe(32)
    active_sessions[token] = {
        'username': username,
        'created_at': time.time()
    }
    return token

def verify_session(token):
    """Check if session token is valid."""
    if token not in active_sessions:
        return False
    
    session = active_sessions[token]
    if time.time() - session['created_at'] > SESSION_TIMEOUT:
        del active_sessions[token]
        return False
    
    return True

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        if not verify_session(token):
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def debug_csv_file():
    """Debug function to check CSV file contents."""
    try:
        print(f"\n🔍 DEBUGGING CSV FILE:")
        print(f"📁 Full path: {os.path.abspath(USER_CSV_PATH)}")
        print(f"📂 File exists: {os.path.exists(USER_CSV_PATH)}")
        
        if os.path.exists(USER_CSV_PATH):
            with open(USER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
                content = file.read()
                print(f"📄 Raw content:\n{repr(content)}")
                
            with open(USER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                print(f"📋 Headers: {reader.fieldnames}")
                
                for i, row in enumerate(reader):
                    print(f"📝 Row {i}: {dict(row)}")
        
        print("🔍 DEBUG COMPLETE\n")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")

def ensure_user_csv_exists():
    """Create user.csv with default admin user if it doesn't exist."""
    dataframe_dir = os.path.dirname(USER_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    print(f"🔍 Checking user file at: {os.path.abspath(USER_CSV_PATH)}")
    
    if not os.path.exists(USER_CSV_PATH):
        print("📝 Creating new user.csv with default admin user")
        default_password_hash = hashlib.sha256("password".encode()).hexdigest()
        
        with open(USER_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Clean headers without extra spaces
            writer.writerow(['username', 'password'])
            writer.writerow(['admin', default_password_hash])
        
        print("✅ Created user.csv successfully")
        print("   Username: admin")
        print("   Password: password")
    else:
        print("📂 Found existing user.csv file")
        # Debug the existing file
        debug_csv_file()

def load_user_credentials():
    """Load user credentials from CSV with robust header handling."""
    ensure_user_csv_exists()
    
    try:
        with open(USER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            users = {}
            
            print(f"📂 Loading credentials from: {USER_CSV_PATH}")
            print(f"📋 CSV headers detected: {reader.fieldnames}")
            
            for row in reader:
                # Handle potential whitespace in headers
                username = None
                password_field = None
                
                # Find username field (case insensitive, strip whitespace)
                for key, value in row.items():
                    clean_key = key.strip().lower()
                    if clean_key == 'username':
                        username = value.strip()
                    elif clean_key == 'password':
                        password_field = value.strip()
                
                if not username or not password_field:
                    print(f"⚠️ Skipping invalid row: {row}")
                    continue
                
                print(f"👤 Found user: {username}")
                
                # Check if password is already hashed (64 chars = SHA-256 hex)
                if len(password_field) == 64 and all(c in '0123456789abcdef' for c in password_field.lower()):
                    print(f"✅ Password already hashed for {username}")
                    users[username] = password_field
                else:
                    print(f"🔄 Hashing plaintext password for {username}")
                    hashed = hashlib.sha256(password_field.encode()).hexdigest()
                    users[username] = hashed
                    # Update the CSV file with hashed password
                    update_user_password(username, hashed)
            
            print(f"📊 Loaded {len(users)} user(s)")
            return users
            
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        print(f"📁 Checked path: {os.path.abspath(USER_CSV_PATH)}")
        return {}

def update_user_password(username, password_hash):
    """Update user password in CSV file with robust header handling."""
    try:
        # Read all users
        users = []
        original_headers = None
        
        with open(USER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            original_headers = reader.fieldnames
            
            for row in reader:
                # Find the username field (handle whitespace)
                row_username = None
                for key, value in row.items():
                    if key.strip().lower() == 'username':
                        row_username = value.strip()
                        break
                
                if row_username == username:
                    # Update password field (handle whitespace in header)
                    for key in row.keys():
                        if key.strip().lower() == 'password':
                            row[key] = password_hash
                            break
                    print(f"🔄 Updated password hash for user '{username}'")
                
                users.append(row)
        
        # Write back to file with original headers
        if users and original_headers:
            with open(USER_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=original_headers)
                writer.writeheader()
                writer.writerows(users)
            print(f"✅ CSV file updated successfully")
        
    except Exception as e:
        print(f"❌ Error updating user password: {e}")
        print(f"📁 File path: {os.path.abspath(USER_CSV_PATH)}")

def register_auth_routes(app):
    """Register authentication routes."""
    
    @app.route('/debug-csv', methods=['GET'])
    def debug_csv():
        """Debug endpoint to check CSV file."""
        debug_csv_file()
        return jsonify({"message": "Check console for CSV debug info"})
    
    @app.route('/login', methods=['POST', 'OPTIONS'])
    def login():
        if request.method == 'OPTIONS':
            return '', 200
        
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            password_hash = data.get('password', '')
            
            if not username or not password_hash:
                return jsonify({
                    'success': False,
                    'message': 'Username and password required'
                }), 400
            
            print(f"🔐 Login attempt for user: {username}")
            users = load_user_credentials()
            print(f"📊 Available users: {list(users.keys())}")
            
            if username in users and users[username] == password_hash:
                token = create_session(username)
                print(f"✅ User '{username}' logged in successfully")
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'token': token,
                    'username': username
                })
            else:
                print(f"❌ Failed login for '{username}' - Invalid credentials")
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password'
                }), 401
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return jsonify({
                'success': False,
                'message': 'Server error'
            }), 500
    
    @app.route('/logout', methods=['POST', 'OPTIONS'])
    def logout():
        if request.method == 'OPTIONS':
            return '', 200
        
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                if token in active_sessions:
                    username = active_sessions[token]['username']
                    del active_sessions[token]
                    print(f"👋 User '{username}' logged out")
            
            return jsonify({'success': True, 'message': 'Logged out'})
        except Exception as e:
            print(f"Logout error: {e}")
            return jsonify({'success': True, 'message': 'Logged out'})