/**
 * Main application script for crypto trading bot frontend with authentication
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

const API_BASE_URL = 'http://localhost:5000';

// Application state
let lastConnectionCheck = null;
let currentLoopInterval = 60;
let statusCheckInterval = null;
let tradesRefreshInterval = null;

/**
 * Get authentication headers for API calls
 */
function getAuthHeaders() {
    const token = sessionStorage.getItem('authToken');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

/**
 * Handle authentication errors
 */
function handleAuthError(response) {
    if (response.status === 401) {
        console.log('🔐 Authentication expired, redirecting to login...');
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('username');
        window.location.href = 'login.html';
        return true;
    }
    return false;
}

/**
 * Make authenticated API request
 */
async function authenticatedFetch(url, options = {}) {
    const authHeaders = getAuthHeaders();
    
    const requestOptions = {
        ...options,
        headers: {
            ...authHeaders,
            ...options.headers
        }
    };
    
    console.log('📡 Making authenticated request to:', url);
    const response = await fetch(url, requestOptions);
    
    if (handleAuthError(response)) {
        throw new Error('Authentication failed');
    }
    
    return response;
}

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Main application initializing...');
    
    if (sessionStorage.getItem('authToken')) {
        loadConfiguration();
        checkStatus();
        loadTrades();
        setupDynamicRefresh();
        console.log('✅ Main application initialized');
    }
});

/**
 * Setup refresh intervals
 */
async function setupDynamicRefresh() {
    await updateLoopInterval();
    statusCheckInterval = setInterval(checkStatus, 10000);
    setupTradesRefresh();
    setInterval(updateLoopInterval, 120000);
    console.log(`⏱️ Dynamic refresh setup complete`);
}

/**
 * Update loop interval from backend
 */
async function updateLoopInterval() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/parameters`);
        if (response.ok) {
            const data = await response.json();
            if (data.current_parameters && data.current_parameters.loop_interval) {
                const newInterval = data.current_parameters.loop_interval;
                if (newInterval !== currentLoopInterval) {
                    console.log(`⏱️ Loop interval updated: ${currentLoopInterval}s → ${newInterval}s`);
                    currentLoopInterval = newInterval;
                    setupTradesRefresh();
                }
            }
        }
    } catch (error) {
        console.log('📊 Using default loop interval:', currentLoopInterval);
    }
}

/**
 * Setup trades refresh interval
 */
function setupTradesRefresh() {
    if (tradesRefreshInterval) {
        clearInterval(tradesRefreshInterval);
    }
    const refreshRate = (currentLoopInterval + 10) * 1000;
    tradesRefreshInterval = setInterval(loadTrades, refreshRate);
    console.log(`📈 Trades refresh: every ${currentLoopInterval + 10}s`);
}

/**
 * Check bot status
 */
async function checkStatus() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/status`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        updateStatusDisplay(data);
        hideMessage('controlMessage');
        
    } catch (error) {
        console.error('📡 Status check error:', error);
        handleStatusError();
    }
}

/**
 * Update status display
 */
function updateStatusDisplay(data) {
    const statusText = document.getElementById('statusText');
    const statusIndicator = document.getElementById('statusIndicator');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    if (data.status === 'running') {
        if (data.indicators && !data.indicators.available) {
            const current = data.data_stats?.total_records || 0;
            const required = data.indicators.min_required || 26;
            statusText.textContent = `Collecting data (${current}/${required})`;
        } else {
            statusText.textContent = `Running - Updates every ${currentLoopInterval}s`;
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
 * Handle status errors
 */
function handleStatusError() {
    document.getElementById('statusText').textContent = 'Backend Offline';
    document.getElementById('statusIndicator').classList.remove('running');
    
    if (!lastConnectionCheck || Date.now() - lastConnectionCheck > 30000) {
        showMessage('controlMessage', 'Backend not running. Start Python backend (main.py) to connect.', 'warning');
        lastConnectionCheck = Date.now();
    }
    
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
}

/**
 * Load trades
 */
async function loadTrades() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/trades`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        updateTradesTable(data.trades);
        
        if (data.trades && data.trades.length > 0) {
            console.log(`📈 Trades updated: ${data.trades.length} trades`);
        }
        
    } catch (error) {
        console.log('📈 Trades not available:', error.message);
    }
}

/**
 * Update trades table
 */
function updateTradesTable(trades) {
    const tableBody = document.getElementById('tradesTableBody');
    tableBody.innerHTML = '';
    
    if (!trades || trades.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" style="text-align: center; color: #64748b;">No trades yet</td>';
        tableBody.appendChild(row);
        return;
    }
    
    trades.reverse().forEach(trade => {
        const row = document.createElement('tr');
        const formattedDate = new Date(trade.datetime).toLocaleString();
        const sideClass = trade.side.toLowerCase();
        const formattedPrice = `${trade.price.toLocaleString('en-US', {
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2
        })}`;
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td><span class="trade-side ${sideClass}">${trade.side}</span></td>
            <td>${formattedPrice}</td>
            <td>${trade.quantity.toFixed(6)}</td>
            <td>${trade.trade_size.toFixed(6)}</td>
        `;
        tableBody.appendChild(row);
    });
}

/**
 * Start bot
 */
function startBot() {
    showMessage('controlMessage', 'The bot starts automatically when you run the Python backend (main.py)', 'warning');
}

/**
 * Stop bot
 */
async function stopBot() {
    const stopBtn = document.getElementById('stopBtn');
    const stopText = document.getElementById('stopText');
    
    stopBtn.disabled = true;
    stopText.innerHTML = '<span class="loading"></span> Stopping...';
    
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/end`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        showMessage('controlMessage', 'Bot shutdown initiated!', 'success');
        
        if (statusCheckInterval) clearInterval(statusCheckInterval);
        if (tradesRefreshInterval) clearInterval(tradesRefreshInterval);
        
        setTimeout(() => {
            document.getElementById('statusText').textContent = 'Stopped';
            document.getElementById('statusIndicator').classList.remove('running');
            stopBtn.disabled = true;
            document.getElementById('startBtn').disabled = false;
        }, 1000);
        
    } catch (error) {
        showMessage('controlMessage', 'Failed to stop bot', 'error');
    } finally {
        setTimeout(() => {
            stopBtn.disabled = false;
            stopText.textContent = 'Stop Bot';
        }, 3000);
    }
}

/**
 * Load configuration
 */
async function loadConfiguration() {
    try {
        console.log('⚙️ Loading configuration...');
        const response = await authenticatedFetch(`${API_BASE_URL}/parameters`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.current_parameters) {
            populateFormFields(data.current_parameters);
            if (data.current_parameters.loop_interval) {
                currentLoopInterval = data.current_parameters.loop_interval;
            }
            console.log('✅ Configuration loaded');
        } else {
            resetToDefaults();
        }
    } catch (error) {
        console.log('⚙️ Could not load configuration, using defaults');
        resetToDefaults();
    }
}

/**
 * Populate form fields
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
 * Reset to defaults
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
 * Save configuration
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

        console.log('💾 Saving configuration...', config);
        const response = await authenticatedFetch(`${API_BASE_URL}/save-config`, {
            method: 'POST',
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        if (config.loop_interval !== currentLoopInterval) {
            currentLoopInterval = config.loop_interval;
            setTimeout(() => {
                setupDynamicRefresh();
            }, 1000);
        }
        
        showMessage('configMessage', 'Configuration saved successfully!', 'success');
        console.log('✅ Configuration saved');
        
    } catch (error) {
        console.error('❌ Save configuration error:', error);
        showMessage('configMessage', `Failed to save: ${error.message}`, 'error');
    } finally {
        saveText.textContent = originalText;
    }
}

/**
 * Get form configuration
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
 * Validate configuration
 */
function validateConfiguration(config) {
    // Check for NaN values
    for (const [key, value] of Object.entries(config)) {
        if (isNaN(value)) {
            showMessage('configMessage', `Invalid value for ${key}`, 'error');
            return false;
        }
    }

    if (config.rsi_buy_threshold >= config.rsi_sell_threshold) {
        showMessage('configMessage', 'RSI buy threshold must be less than sell threshold', 'error');
        return false;
    }
    
    if (config.stop_loss <= 0 || config.stop_profit <= 0) {
        showMessage('configMessage', 'Stop loss and take profit must be greater than 0', 'error');
        return false;
    }
    
    return true;
}

/**
 * Show message
 */
function showMessage(elementId, text, type) {
    const messageDiv = document.getElementById(elementId);
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        if (type === 'success') {
            setTimeout(() => hideMessage(elementId), 8000);
        }
    }
}

/**
 * Hide message
 */
function hideMessage(elementId) {
    const messageDiv = document.getElementById(elementId);
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}

console.log('🚀 Main application script with authentication loaded!');