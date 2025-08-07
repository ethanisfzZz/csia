# CompSci Internal Assessment Crypto Trading Bot

## Brief Description

This trading bot automates Binance cryptocurrency trading for Bitcoin (BTC) with trade logic based on MACD trading. This Bot allows for full customization of trading thresholds to tailor to your trading needs!

## Installation & Setup Guide

### Prerequisites & Repository Setup

1. **Clone the repository**: 
   ```bash
   git clone https://github.com/ethanisfzZz/csia
   cd crypto-trading-bot
   ```

2. **Install Miniconda**: Download from https://docs.conda.io/en/latest/miniconda.html

3. **Initialize conda** (required for first-time setup):
   ```bash
   conda init
   # Restart your terminal or run: source ~/.bashrc (Linux/Mac) or restart Command Prompt (Windows)
   ```

### Installation Guide (macOS & Windows)

1. **Extract project files** to a folder (if not using git clone)
2. **Open Terminal (macOS) or Command Prompt (Windows)** and navigate to the project folder
3. **Create and activate environment**: 
   ```bash
   conda env create -f Backend/environment.yml
   conda activate csia
   ```
4. **Test installation**: `python -c "import pandas, requests, ta, flask; print('Ready!')"`






### How to Launch Bot

1. **Activate environment**: `conda activate csia`
2. **Navigate to Backend folder**: `cd Backend`
3. **Start the bot**: `python main.py`
4. **Navigate to frontend:** `cd Frontend`
5. **Start PNPM:** `pnpm start`




## User Guide

1. **Access web interface**: 
   - **Option 1**: Open browser to `http://localhost:3000/login.html` 
   - **Option 2**: Open `Frontend/login.html` in your browser (connects to localhost:5000 API)
2. **Login**: Use `admin` / `Password123@` for first login
3. **Wait for data collection**: Bot needs 26+ data points before trading (takes ~26 minutes)


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