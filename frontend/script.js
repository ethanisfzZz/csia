/**
 * Main application script for crypto trading bot frontend
 * Handles core functionality: status checking, trade loading, configuration
 * Now syncs with backend loop_interval for optimal refresh timing
 */

// Configuration constants
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

// API configuration
const API_BASE_URL = 'http://localhost:5000';

// Application state
let lastConnectionCheck = null;
let currentLoopInterval = 60; // Will be updated from backend
let statusCheckInterval = null;
let tradesRefreshInterval = null;

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Main application initializing...');
    
    // Load initial data
    loadConfiguration();
    checkStatus();
    loadTrades();
    
    // Setup dynamic intervals based on backend configuration
    setupDynamicRefresh();
    
    console.log('✅ Main application initialized');
});

/**
 * Setup refresh intervals that sync with backend configuration
 */
async function setupDynamicRefresh() {
    // Get initial loop interval from backend
    await updateLoopInterval();
    
    // Setup status checking (every 10 seconds - independent of loop interval)
    statusCheckInterval = setInterval(checkStatus, 10000);
    
    // Setup trades refresh based on loop interval
    setupTradesRefresh();
    
    // Check for loop interval changes every 2 minutes
    setInterval(updateLoopInterval, 120000);
    
    console.log(`⏱️ Dynamic refresh setup complete - trades refresh every ${currentLoopInterval + 10}s`);
}

/**
 * Update loop interval from backend configuration
 */
async function updateLoopInterval() {
    try {
        const response = await fetch(`${API_BASE_URL}/parameters`);
        if (response.ok) {
            const data = await response.json();
            if (data.current_parameters && data.current_parameters.loop_interval) {
                const newInterval = data.current_parameters.loop_interval;
                
                if (newInterval !== currentLoopInterval) {
                    console.log(`⏱️ Loop interval updated: ${currentLoopInterval}s → ${newInterval}s`);
                    currentLoopInterval = newInterval;
                    
                    // Restart trades refresh with new interval
                    setupTradesRefresh();
                }
            }
        }
    } catch (error) {
        console.log('Using default loop interval:', currentLoopInterval);
    }
}

/**
 * Setup trades refresh interval based on current loop interval
 */
function setupTradesRefresh() {
    // Clear existing interval
    if (tradesRefreshInterval) {
        clearInterval(tradesRefreshInterval);
    }
    
    // Refresh trades slightly after backend updates (add 10s buffer)
    const refreshRate = (currentLoopInterval + 10) * 1000;
    
    tradesRefreshInterval = setInterval(loadTrades, refreshRate);
    console.log(`📈 Trades refresh set to every ${currentLoopInterval + 10} seconds`);
}

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
        updateStatusDisplay(data);
        hideMessage('controlMessage');
        
    } catch (error) {
        console.error('Status check error:', error);
        handleStatusError();
    }
}

/**
 * Update status display elements with enhanced information
 */
function updateStatusDisplay(data) {
    const statusText = document.getElementById('statusText');
    const statusIndicator = document.getElementById('statusIndicator');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    console.log('Status response:', data);
    
    if (data.status === 'running') {
        // Check if indicators are ready
        if (data.indicators && typeof data.indicators.available !== 'undefined') {
            if (!data.indicators.available) {
                const current = data.data_stats?.total_records || data.data_stats?.cached_records || 0;
                const required = data.indicators.min_required || 26;
                statusText.textContent = `Collecting data (${current}/${required}) - Next update in ${currentLoopInterval}s`;
            } else {
                statusText.textContent = `Running - Updates every ${currentLoopInterval}s`;
            }
        } else {
            // Fallback logic
            const current = data.data_stats?.total_records || data.data_stats?.cached_records || 0;
            if (current < 26) {
                statusText.textContent = `Collecting data (${current}/26) - Next update in ${currentLoopInterval}s`;
            } else {
                statusText.textContent = `Running - Updates every ${currentLoopInterval}s`;
            }
        }
        
        statusIndicator.classList.add('running');
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        statusText.textContent = 'Stopped';
        statusIndicator.classList.remove('running');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

/**
 * Handle status check errors
 */
function handleStatusError() {
    document.getElementById('statusText').textContent = 'Backend Offline';
    document.getElementById('statusIndicator').classList.remove('running');
    
    // Show connection error message (throttled)
    if (!lastConnectionCheck || Date.now() - lastConnectionCheck > 30000) {
        showMessage('controlMessage', 'Backend not running. Start Python backend (main.py) to connect.', 'warning');
        lastConnectionCheck = Date.now();
    }
    
    // Reset buttons when backend is offline
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
}

/**
 * Load and display trades from the backend
 */
async function loadTrades() {
    try {
        const response = await fetch(`${API_BASE_URL}/trades`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        updateTradesTable(data.trades);
        
        // Log when trades are updated
        if (data.trades && data.trades.length > 0) {
            console.log(`📈 Trades table updated with ${data.trades.length} trades`);
        }
        
    } catch (error) {
        console.log('Trades not available:', error.message);
    }
}

/**
 * Update trades table with trade data
 */
function updateTradesTable(trades) {
    const tableBody = document.getElementById('tradesTableBody');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (!trades || trades.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" style="text-align: center; color: #64748b;">No trades yet</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // Add trades (most recent first)
    trades.reverse().forEach(trade => {
        const row = document.createElement('tr');
        
        const formattedDate = new Date(trade.datetime).toLocaleString();
        const sideClass = trade.side.toLowerCase();
        const formattedPrice = `${trade.price.toLocaleString('en-US', {
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2
        })}`;
        const formattedQuantity = trade.quantity.toFixed(6);
        const formattedTradeSize = trade.trade_size.toFixed(6);
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td><span class="trade-side ${sideClass}">${trade.side}</span></td>
            <td>${formattedPrice}</td>
            <td>${formattedQuantity}</td>
            <td>${formattedTradeSize}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Start the trading bot
 */
function startBot() {
    showMessage('controlMessage', 'The bot starts automatically when you run the Python backend (main.py)', 'warning');
}

/**
 * Stop the trading bot
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
        
        // Clear all intervals when stopping
        if (statusCheckInterval) clearInterval(statusCheckInterval);
        if (tradesRefreshInterval) clearInterval(tradesRefreshInterval);
        
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
            populateFormFields(data.current_parameters);
            
            // Update current loop interval from loaded config
            if (data.current_parameters.loop_interval) {
                currentLoopInterval = data.current_parameters.loop_interval;
                console.log(`⏱️ Loaded loop interval: ${currentLoopInterval}s`);
            }
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
 * Save configuration to the backend
 */
async function saveConfiguration() {
    const saveText = document.getElementById('saveText');
    const originalText = saveText.textContent;
    
    saveText.innerHTML = '<span class="loading"></span> Saving...';
    
    try {
        const config = getFormConfiguration();

        if (!validateConfiguration(config)) {
            return;
        }

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
        
        // Update local loop interval if it changed
        if (config.loop_interval !== currentLoopInterval) {
            console.log(`⏱️ Loop interval will change: ${currentLoopInterval}s → ${config.loop_interval}s`);
            currentLoopInterval = config.loop_interval;
            
            // Restart refresh intervals with new timing
            setTimeout(() => {
                setupDynamicRefresh();
            }, 1000);
        }
        
        showMessage('configMessage', 
            `Configuration saved! Loop interval: ${config.loop_interval}s. Changes take effect on next trading cycle.`, 
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

    // Basic validation rules
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
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        // Auto-hide success messages after 8 seconds
        if (type === 'success') {
            setTimeout(() => hideMessage(elementId), 8000);
        }
    }
}

/**
 * Hide a message
 */
function hideMessage(elementId) {
    const messageDiv = document.getElementById(elementId);
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}

/**
 * Get current refresh timing information for debugging
 */
function getRefreshInfo() {
    return {
        currentLoopInterval: currentLoopInterval,
        statusCheckInterval: !!statusCheckInterval,
        tradesRefreshInterval: !!tradesRefreshInterval,
        tradesRefreshRate: currentLoopInterval + 10
    };
}

// Export refresh info for debugging
window.getRefreshInfo = getRefreshInfo;

console.log('🚀 Main application script loaded!');