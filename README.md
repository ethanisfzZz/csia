# CompSci Internal Assessment Crypto Trading Bot

## Brief Description


This trading bot automates Binance cryptocurrency trading for Bitcoin (BTC) with trade logic based on MACD trading. This Bot allows for full customization of trading thresholds to tailor to your trading needs!


## Installation & Setup Guide

### macOS Installation Guide




1. **Install Miniconda**: Download from https://docs.conda.io/en/latest/miniconda.html
2. **Extract project files** to a folder
3. **Open Terminal** and navigate to the project folder
4. **Create environment**: `conda env create -f Backend/environment.yml`
5. **Activate environment**: `conda activate csia`
6. **Install web components**: `pip install flask-cors`
7. **Test installation**: `python -c "import pandas, requests, ta, flask; print('Ready!')"`

### Windows Installation Guide

1. **Install Miniconda**: Download from https://docs.conda.io/en/latest/miniconda.html
   - ✅ Check "Add to PATH" during installation
2. **Extract project files** to a folder
3. **Open Command Prompt** and navigate to the project folder
4. **Create environment**: `conda env create -f Backend/environment.yml`
5. **Activate environment**: `conda activate csia`
6. **Install web components**: `pip install flask-cors`
7. **Test installation**: `python -c "import pandas, requests, ta, flask; print('Ready!')"`

### How to Launch Bot

1. **Activate environment**: `conda activate csia`
2. **Navigate to Backend folder**: `cd Backend`
3. **Start the bot**: `python main.py`
4. **Open web interface**: Open `Frontend/index.html` in your browser
5. **Wait for data collection**: Bot needs 26+ data points before trading (takes ~26 minutes)






## User Guide

### How to Login

- **Default credentials**: Upon first launch, the default logins are admin:password
- **Access**: Simply open `Frontend/index.html` in your browser

### How to Start/Stop Bot

**Starting the Bot:**
- Bot starts automatically when you run `python main.py`
- Web interface will show "Running" status with green indicator
- Initial phase: "Collecting data" until X data points gathered (Depending on your configuration, defaults to 26)

**Stopping the Bot:**
- Click "Stop Bot" button in web interface, OR
- Press `Ctrl+C` in the terminal running the Python backend
- Status will change to "Stopped" with red indicator



### What the Graph Shows

**Price Chart:**
- **Line**: Real-time Bitcoin price in USD
- **Green triangles (▲)**: Buy orders executed by the bot
- **Red triangles (▼)**: Sell orders executed by the bot
- **Chart states**:
  - *No data*: Bot hasn't started collecting data yet
  - *Insufficient data*: Price line only, collecting data for indicators
  - *Full chart*: Price + trade markers when indicators are ready




### What the Table Shows

**Trading History Table:**
- **Date & Time**: When each trade was executed
- **Side**: BUY (green) or SELL (red) orders
- **Price**: Bitcoin price at time of trade
- **Quantity**: Amount of Bitcoin traded
- **Trade Size**: Position size used for the trade
- **Most recent trades** appear at the top




### How to Configure Threshold Values

**Configuration Panel:** - Press "Save" to save configurations, Press "Reset" to reset values to default values
- **Trade Size**: Amount of BTC per trade (0.001 - 1.0)
- **Stop Loss %**: Maximum loss before auto-sell (0.5% - 10%)
- **Take Profit %**: Target profit for auto-sell (0.5% - 15%)
- **RSI Buy Threshold**: Oversold level to trigger buy (10-40, default: 30)
- **RSI Sell Threshold**: Overbought level to trigger sell (60-90, default: 70)
- **MACD Buy/Sell**: Signal levels for MACD indicator (-0.01 to 0.01)
- **Loop Interval**: Time between decisions in seconds (30-300)
- **Indicator Window**: Period for calculations (10-50, default: 26)