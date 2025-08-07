"""
Simple authentication module for single-user crypto trading bot.
Enhanced security with pre-hashed passwords and reduced attack surface.

Citations:
- SHA-256 hashing: https://docs.python.org/3/library/hashlib.html
- Flask decorators: https://flask.palletsprojects.com/en/2.3.x/patterns/viewdecorators/
- Session management: https://docs.python.org/3/library/secrets.html
- CSV file handling: https://docs.python.org/3/library/csv.html
"""

import os
import csv
import secrets
import time
from functools import wraps
from flask import request, jsonify

# simple in-memory session store - tokens expire after 24 hours
active_sessions = {}
SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds

USER_CSV_PATH = "./dataframe/user.csv"

def create_session(username):
    """Create a new session token using cryptographically secure random generation."""
    token = secrets.token_urlsafe(32)  # generates secure random token
    active_sessions[token] = {
        'username': username,
        'created_at': time.time()
    }
    return token

def verify_session(token):
    """Check if session token is valid and hasn't expired."""
    if token not in active_sessions:
        return False
    
    session = active_sessions[token]
    # check if session has expired
    if time.time() - session['created_at'] > SESSION_TIMEOUT:
        del active_sessions[token]  # cleanup expired session
        return False
    
    return True

def require_auth(f):
    """
    Decorator to require authentication for Flask routes.
    Checks for valid Bearer token in Authorization header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # check for proper authorization header format
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]  # extract token from "Bearer <token>"
        if not verify_session(token):
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        return f(*args, **kwargs)  # call original function if authenticated
    return decorated_function

def ensure_user_csv_exists():
    """Create user.csv with secure default admin user if it doesn't exist."""
    dataframe_dir = os.path.dirname(USER_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)  # create directory if needed
    
    print(f"🔍 Checking user authentication file...")
    
    if not os.path.exists(USER_CSV_PATH):
        print("📝 Creating secure user authentication file")
        # pre-computed SHA-256 hash for enhanced security
        secure_password_hash = "d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c"
        
        with open(USER_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # clean headers without extra spaces to avoid parsing issues
            writer.writerow(['username', 'password'])
            writer.writerow(['admin', secure_password_hash])
        
        print("✅ Secure authentication system initialized")
        print("   Username: admin")
        print("   Password: [Secure - Check documentation]")
    else:
        print("📂 Using existing authentication file")

def load_user_credentials():
    """Load user credentials from CSV with robust header handling."""
    ensure_user_csv_exists()
    
    try:
        with open(USER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            users = {}
            
            print(f"📂 Loading secure credentials...")
            
            for row in reader:
                # handle potential whitespace in headers - common CSV issue
                username = None
                password_field = None
                
                # find username and password fields (case insensitive, strip whitespace)
                for key, value in row.items():
                    clean_key = key.strip().lower()
                    if clean_key == 'username':
                        username = value.strip()
                    elif clean_key == 'password':
                        password_field = value.strip()
                
                if not username or not password_field:
                    print(f"⚠️ Skipping invalid row: {row}")
                    continue
                
                print(f"👤 Authenticated user: {username}")
                
                # password should already be hashed in CSV for security
                if len(password_field) == 64 and all(c in '0123456789abcdef' for c in password_field.lower()):
                    users[username] = password_field
                else:
                    print(f"⚠️ Invalid hash format for user: {username}")
                    continue
            
            print(f"📊 Authentication system ready: {len(users)} user(s)")
            return users
            
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return {}

def register_auth_routes(app):
    """Register authentication routes with the Flask app."""
    
    @app.route('/login', methods=['POST', 'OPTIONS'])
    def login():
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            return '', 200
        
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            password_hash = data.get('password', '')  # frontend sends pre-hashed password
            
            if not username or not password_hash:
                return jsonify({
                    'success': False,
                    'message': 'Username and password required'
                }), 400
            
            print(f"🔐 Authentication attempt for user: {username}")
            users = load_user_credentials()
            
            # verify credentials by comparing hashed passwords
            if username in users and users[username] == password_hash:
                token = create_session(username)  # create new session
                print(f"✅ User '{username}' authenticated successfully")
                
                return jsonify({
                    'success': True,
                    'message': 'Authentication successful',
                    'token': token,
                    'username': username
                })
            else:
                print(f"❌ Authentication failed for '{username}' - Invalid credentials")
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password'
                }), 401
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return jsonify({
                'success': False,
                'message': 'Server error'
            }), 500
    
    @app.route('/logout', methods=['POST', 'OPTIONS'])
    def logout():
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            return '', 200
        
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                if token in active_sessions:
                    username = active_sessions[token]['username']
                    del active_sessions[token]  # remove session from memory
                    print(f"👋 User '{username}' logged out")
            
            return jsonify({'success': True, 'message': 'Logged out'})
        except Exception as e:
            print(f"Logout error: {e}")
            return jsonify({'success': True, 'message': 'Logged out'})  # always return success for logout