// Global variables for chart state
let marketData = [];
let tradeData = [];

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
    loadTrades();
    loadVisualizationData();
    // Check status every 10 seconds
    setInterval(checkStatus, 10000);
    // Refresh trades every 30 seconds
    setInterval(loadTrades, 30000);
    // Refresh visualization every 60 seconds
    setInterval(loadVisualizationData, 60000);
});

/**
 * Load market data and trades for visualization
 */
async function loadVisualizationData() {
    try {
        // Load market data
        const marketResponse = await fetch(`${API_BASE_URL}/market-data`);
        if (marketResponse.ok) {
            const marketResult = await marketResponse.json();
            marketData = marketResult.data || [];
        }

        // Load trades data
        const tradesResponse = await fetch(`${API_BASE_URL}/trades`);
        if (tradesResponse.ok) {
            const tradesResult = await tradesResponse.json();
            tradeData = tradesResult.trades || [];
        }

        // Create visualization
        createPriceChart();

    } catch (error) {
        console.error('Error loading visualization data:', error);
        showMessage('vizMessage', 'Unable to load chart data. Backend may not be running.', 'warning');
    }
}

/**
 * Create price chart with trade markers
 */
function createPriceChart() {
    // Mock data for demonstration if no real data available
    if (marketData.length === 0) {
        createMockPriceChart();
        return;
    }

    const timestamps = marketData.map(d => new Date(d.datetime));
    const prices = marketData.map(d => d.price);

    // Create base price trace
    const priceTrace = {
        x: timestamps,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: 'BTC Price',
        line: {
            color: '#ff6b6b',
            width: 2
        }
    };

    // Add trade markers
    const buyTrades = tradeData.filter(t => t.side === 'BUY');
    const sellTrades = tradeData.filter(t => t.side === 'SELL');

    const buyTrace = {
        x: buyTrades.map(t => new Date(t.datetime)),
        y: buyTrades.map(t => t.price),
        mode: 'markers',
        type: 'scatter',
        name: 'Buy Orders',
        marker: {
            color: '#10b981',
            size: 12,
            symbol: 'triangle-up'
        }
    };

    const sellTrace = {
        x: sellTrades.map(t => new Date(t.datetime)),
        y: sellTrades.map(t => t.price),
        mode: 'markers',
        type: 'scatter',
        name: 'Sell Orders',
        marker: {
            color: '#ef4444',
            size: 12,
            symbol: 'triangle-down'
        }
    };

    const layout = {
        title: 'Bitcoin Price with Trading Activity',
        xaxis: { title: 'Time', color: '#e2e8f0' },
        yaxis: { title: 'Price (USD)', color: '#e2e8f0' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e8f0' }
    };

    const traces = [priceTrace];
    if (buyTrades.length > 0) traces.push(buyTrace);
    if (sellTrades.length > 0) traces.push(sellTrace);

    Plotly.newPlot('priceChart', traces, layout, {responsive: true});
}

/**
 * Create mock price chart for demonstration
 */
function createMockPriceChart() {
    // Generate mock Bitcoin price data
    const now = new Date();
    const mockData = [];
    const mockTrades = [];
    let price = 50000;

    for (let i = 100; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 60000); // 1 minute intervals
        price += (Math.random() - 0.5) * 500; // Random price movement
        price = Math.max(45000, Math.min(55000, price)); // Keep within range
        
        mockData.push({
            datetime: timestamp,
            price: price
        });

        // Add some random trades
        if (Math.random() < 0.1) { // 10% chance of trade
            mockTrades.push({
                datetime: timestamp,
                side: Math.random() > 0.5 ? 'BUY' : 'SELL',
                price: price,
                quantity: 0.01
            });
        }
    }

    const timestamps = mockData.map(d => d.datetime);
    const prices = mockData.map(d => d.price);

    const priceTrace = {
        x: timestamps,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: 'BTC Price (Demo)',
        line: {
            color: '#ff6b6b',
            width: 2
        }
    };

    const buyTrades = mockTrades.filter(t => t.side === 'BUY');
    const sellTrades = mockTrades.filter(t => t.side === 'SELL');

    const buyTrace = {
        x: buyTrades.map(t => t.datetime),
        y: buyTrades.map(t => t.price),
        mode: 'markers',
        type: 'scatter',
        name: 'Buy Orders',
        marker: {
            color: '#10b981',
            size: 12,
            symbol: 'triangle-up'
        }
    };

    const sellTrace = {
        x: sellTrades.map(t => t.datetime),
        y: sellTrades.map(t => t.price),
        mode: 'markers',
        type: 'scatter',
        name: 'Sell Orders',
        marker: {
            color: '#ef4444',
            size: 12,
            symbol: 'triangle-down'
        }
    };

    const layout = {
        title: 'Bitcoin Price with Trading Activity (Demo Data)',
        xaxis: { title: 'Time', color: '#e2e8f0' },
        yaxis: { title: 'Price (USD)', color: '#e2e8f0' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e8f0' }
    };

    const traces = [priceTrace, buyTrace, sellTrace];
    Plotly.newPlot('priceChart', traces, layout, {responsive: true});
}

/**
 * Refresh visualization data and charts
 */
function refreshVisualization() {
    const refreshText = document.getElementById('refreshText');
    const originalText = refreshText.textContent;
    
    refreshText.innerHTML = '<span class="loading"></span> Refreshing...';
    
    loadVisualizationData().then(() => {
        showMessage('vizMessage', 'Chart refreshed successfully!', 'success');
        setTimeout(() => {
            refreshText.textContent = originalText;