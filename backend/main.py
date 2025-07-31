"""
Main application entry point for the crypto trading bot with authentication.
"""

from api_routes import create_app, register_routes
from trading_bot import start_background_trading
from auth import ensure_user_csv_exists

def main():
    """Main application entry point"""
    print("🚀 Starting Crypto Trading Bot with Authentication...")
    print("="*60)
    
    # Initialize authentication
    print("🔐 Initializing authentication system...")
    ensure_user_csv_exists()
    
    # Create Flask app
    app = create_app()
    
    # Register routes (includes auth routes)
    register_routes(app)
    
    # Start background trading
    print("🤖 Starting background trading system...")
    start_background_trading()
    
    print("="*60)
    print("🌐 CRYPTO TRADING BOT READY!")
    print("="*60)
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
    
    # Start Flask server
    try:
        app.run(debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")

if __name__ == '__main__':
    main()