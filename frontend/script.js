// Default configuration values (matching the backend defaults)
const DEFAULT_CONFIG = {
    tradeSize: 0.01,
    stopLoss: 2.0,
    stopProfit: 2.5,
    rsiBuy: 30,
    rsiSell: 70,
    macdBuy: 0.0,
    macdSell: 0.0,
    positionSize: 100.0,
    loopInterval: 60,
    indicatorWindow: 26,
    active: 1
};

// API base URL - change this to match your backend
const API_BASE_URL = 'http://localhost:5000';

// Check status when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadConfiguration();
    checkStatus();
    // Check status every 10 seconds
    setInterval(checkStatus, 10000);
});

/**
 * Check the current status of the trading bot
 */
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        const statusText = document.getElementById('statusText');
        const statusIndicator = document.getElementById('statusIndicator');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (data.status === 'running') {
            statusText.textContent = 'Running';
            statusIndicator.classList.add('running');
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusText.textContent = 'Stopped';
            statusIndicator.classList.remove('running');
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
        
        hideMessage('controlMessage');
        
    } catch (error) {
        document.getElementById('statusText').textContent = 'Offline';
        document.getElementById('statusIndicator').classList.remove('running');
        
        // Only show connection error if it's the first check or if it's been a while
        if (!window.lastConnectionCheck || Date.now() - window.lastConnectionCheck > 30000) {
            showMessage('controlMessage', 'Backend not running. Start the Python backend to connect.', 'warning');
            window.lastConnectionCheck = Date.now();
        }
    }
}

/**
 * Start the trading bot (Note: Bot actually starts when backend runs)
 */
async function startBot() {
    showMessage('controlMessage', 'The bot starts automatically when you run the Python backend (main.py)', 'warning');
}

/**
 * Stop the trading bot - Now properly shuts down the entire application
 */
async function stopBot() {
    const stopBtn = document.getElementById('stopBtn');
    const stopText = document.getElementById('stopText');
    
    stopBtn.disabled = true;
    stopText.innerHTML = '<span class="loading"></span> Stopping...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/end`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        showMessage('controlMessage', 'Bot shutdown initiated! The application will terminate in 2 seconds.', 'success');
        
        // Update UI to show stopped state immediately
        setTimeout(() => {
            document.getElementById('statusText').textContent = 'Stopped';
            document.getElementById('statusIndicator').classList.remove('running');
            stopBtn.disabled = true;
            document.getElementById('startBtn').disabled = false;
        }, 1000);
        
    } catch (error) {
        showMessage('controlMessage', 'Failed to stop bot - make sure backend is running', 'error');
    } finally {
        // Reset button text after a delay
        setTimeout(() => {
            stopBtn.disabled = false;
            stopText.textContent = 'Stop Bot';
        }, 3000);
    }
}

/**
 * Load configuration from the backend
 */
async function loadConfiguration() {
    try {
        const response = await fetch(`${API_BASE_URL}/parameters`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.current_parameters) {
            const params = data.current_parameters;
            populateFormFields(params);
        } else {
            resetToDefaults();
        }
    } catch (error) {
        console.log('Could not load configuration from backend, using defaults');
        resetToDefaults();
    }
}

/**
 * Populate form fields with configuration data
 */
function populateFormFields(params) {
    document.getElementById('tradeSize').value = params.trade_size || DEFAULT_CONFIG.tradeSize;
    document.getElementById('stopLoss').value = ((params.stop_loss || DEFAULT_CONFIG.stopLoss / 100) * 100).toFixed(1);
    document.getElementById('stopProfit').value = ((params.stop_profit || DEFAULT_CONFIG.stopProfit / 100) * 100).toFixed(1);
    document.getElementById('rsiBuy').value = params.rsi_buy_threshold || DEFAULT_CONFIG.rsiBuy;
    document.getElementById('rsiSell').value = params.rsi_sell_threshold || DEFAULT_CONFIG.rsiSell;
    document.getElementById('macdBuy').value = params.macd_buy_threshold || DEFAULT_CONFIG.macdBuy;
    document.getElementById('macdSell').value = params.macd_sell_threshold || DEFAULT_CONFIG.macdSell;
    document.getElementById('positionSize').value = params.position_size_usdt || DEFAULT_CONFIG.positionSize;
    document.getElementById('loopInterval').value = params.loop_interval || DEFAULT_CONFIG.loopInterval;
    document.getElementById('indicatorWindow').value = params.indicator_window || DEFAULT_CONFIG.indicatorWindow;
    document.getElementById('active').value = params.active ? 1 : 0;
}

/**
 * Reset all form fields to default values
 */
function resetToDefaults() {
    document.getElementById('tradeSize').value = DEFAULT_CONFIG.tradeSize;
    document.getElementById('stopLoss').value = DEFAULT_CONFIG.stopLoss;
    document.getElementById('stopProfit').value = DEFAULT_CONFIG.stopProfit;
    document.getElementById('rsiBuy').value = DEFAULT_CONFIG.rsiBuy;
    document.getElementById('rsiSell').value = DEFAULT_CONFIG.rsiSell;
    document.getElementById('macdBuy').value = DEFAULT_CONFIG.macdBuy;
    document.getElementById('macdSell').value = DEFAULT_CONFIG.macdSell;
    document.getElementById('positionSize').value = DEFAULT_CONFIG.positionSize;
    document.getElementById('loopInterval').value = DEFAULT_CONFIG.loopInterval;
    document.getElementById('indicatorWindow').value = DEFAULT_CONFIG.indicatorWindow;
    document.getElementById('active').value = DEFAULT_CONFIG.active;
    
    showMessage('configMessage', 'Configuration reset to default values', 'success');
}

/**
 * Save configuration directly to the backend's threshold.csv file
 */
async function saveConfiguration() {
    const saveText = document.getElementById('saveText');
    const originalText = saveText.textContent;
    
    saveText.innerHTML = '<span class="loading"></span> Saving...';
    
    try {
        // Get form values
        const config = getFormConfiguration();

        // Validate configuration
        if (!validateConfiguration(config)) {
            return;
        }

        // Send configuration to backend
        const response = await fetch(`${API_BASE_URL}/save-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const result = await response.json();
        
        showMessage('configMessage', 
            'Configuration saved successfully to backend! Changes will take effect on the next trading loop iteration.', 
            'success'
        );
        
    } catch (error) {
        console.error('Save configuration error:', error);
        showMessage('configMessage', `Failed to save configuration: ${error.message}`, 'error');
    } finally {
        saveText.textContent = originalText;
    }
}

/**
 * Get configuration from form fields
 */
function getFormConfiguration() {
    return {
        trade_size: parseFloat(document.getElementById('tradeSize').value),
        stop_loss: parseFloat(document.getElementById('stopLoss').value) / 100,
        stop_profit: parseFloat(document.getElementById('stopProfit').value) / 100,
        rsi_buy_threshold: parseInt(document.getElementById('rsiBuy').value),
        rsi_sell_threshold: parseInt(document.getElementById('rsiSell').value),
        macd_buy_threshold: parseFloat(document.getElementById('macdBuy').value),
        macd_sell_threshold: parseFloat(document.getElementById('macdSell').value),
        position_size_usdt: parseFloat(document.getElementById('positionSize').value),
        loop_interval: parseInt(document.getElementById('loopInterval').value),
        indicator_window: parseInt(document.getElementById('indicatorWindow').value),
        active: parseInt(document.getElementById('active').value)
    };
}

/**
 * Validate configuration values
 */
function validateConfiguration(config) {
    // Check for NaN values
    for (const [key, value] of Object.entries(config)) {
        if (isNaN(value)) {
            showMessage('configMessage', `Invalid value for ${key}. Please enter a valid number.`, 'error');
            return false;
        }
    }

    // Basic validation
    if (config.rsi_buy_threshold >= config.rsi_sell_threshold) {
        showMessage('configMessage', 'RSI buy threshold must be less than sell threshold', 'error');
        return false;
    }
    
    if (config.stop_loss <= 0 || config.stop_profit <= 0) {
        showMessage('configMessage', 'Stop loss and take profit must be greater than 0', 'error');
        return false;
    }
    
    if (config.trade_size <= 0 || config.position_size_usdt <= 0) {
        showMessage('configMessage', 'Trade size and position size must be greater than 0', 'error');
        return false;
    }
    
    if (config.loop_interval < 30) {
        showMessage('configMessage', 'Loop interval must be at least 30 seconds', 'error');
        return false;
    }
    
    if (config.indicator_window < 10) {
        showMessage('configMessage', 'Indicator window must be at least 10', 'error');
        return false;
    }

    // Range validations
    if (config.trade_size < 0.001 || config.trade_size > 1.0) {
        showMessage('configMessage', 'Trade size must be between 0.001 and 1.0', 'error');
        return false;
    }

    if (config.rsi_buy_threshold < 10 || config.rsi_buy_threshold > 40) {
        showMessage('configMessage', 'RSI buy threshold must be between 10 and 40', 'error');
        return false;
    }

    if (config.rsi_sell_threshold < 60 || config.rsi_sell_threshold > 90) {
        showMessage('configMessage', 'RSI sell threshold must be between 60 and 90', 'error');
        return false;
    }
    
    return true;
}

/**
 * Show a message to the user
 */
function showMessage(elementId, text, type) {
    const messageDiv = document.getElementById(elementId);
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    // Auto-hide success messages after 8 seconds
    if (type === 'success') {
        setTimeout(() => hideMessage(elementId), 8000);
    }
}

/**
 * Hide a message
 */
function hideMessage(elementId) {
    const messageDiv = document.getElementById(elementId);
    messageDiv.style.display = 'none';
}