"""
Main application entry point for the crypto trading bot with authentication.

Citations:
- Flask application factory pattern: https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/
- Background threading in Python: https://docs.python.org/3/library/threading.html
- Application startup patterns: https://realpython.com/python-application-layouts/
"""

from api_routes import create_app, register_routes
from trading_bot import start_background_trading
from auth import ensure_user_csv_exists

def main():
    """
    Main application entry point - orchestrates the startup of both web interface and trading engine.
    Follows a structured startup sequence to ensure all components are properly initialized.
    """
    print("🚀 Starting Crypto Trading Bot with Authentication...")
    print("="*60)
    
    # initialize authentication system first - critical for security
    print("🔐 Initializing authentication system...")
    ensure_user_csv_exists()  # creates default admin user if needed
    
    # create Flask app using factory pattern for better organization
    app = create_app()
    
    # register all routes (includes both API and auth endpoints)
    register_routes(app)
    
    # start background trading system in separate thread
    print("🤖 Starting background trading system...")
    start_background_trading()  # non-blocking - runs in daemon thread
    
    print("="*60)
    print("🌐 CRYPTO TRADING BOT READY!")
    print("="*60)
    # provide clear user instructions for accessing the system
    print("📱 Web Interface:")
    print("   🔑 Login: http://localhost:5000/login.html")
    print("   📊 Dashboard: http://localhost:5000/index.html")
    print("   🔧 API: http://localhost:5000/")
    print("   🐛 Debug CSV: http://localhost:5000/debug-csv")
    print()
    print("🔑 Default Login:")
    print("   Username: admin")
    print("   Password: password")
    print("="*60)
    print("Press Ctrl+C to stop")
    print()
    
    # start Flask development server - this blocks until shutdown
    try:
        # debug=True enables auto-reload, use_reloader=False prevents double startup with threading
        app.run(debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")

if __name__ == '__main__':
    main()  # entry point when script is run directly