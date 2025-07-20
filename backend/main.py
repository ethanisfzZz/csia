"""
Main application entry point for the crypto trading bot.
Initializes and starts the Flask web server and background trading loop.
"""

from api_routes import create_app, register_routes
from trading_bot import start_background_trading

def main():
    """Main application entry point"""
    print("Starting Trading Bot...")
    print("Press Ctrl+C to stop the application")
    
    # Create Flask app
    app = create_app()
    
    # Register API routes
    register_routes(app)
    
    # Start background trading loop BEFORE starting Flask
    start_background_trading()
    
    # Start Flask API (this runs the web server)
    app.run(debug=True, use_reloader=False)  # use_reloader=False prevents double threading

if __name__ == '__main__':
    main()