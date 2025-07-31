/**
 * Handles three data states: no data, insufficient data, and full data with indicators
 */
class TradingChartManager {
    constructor(apiBaseUrl = 'http://localhost:5000') {
        this.marketData = [];
        this.tradeData = [];
        this.API_BASE_URL = apiBaseUrl;
        this.chartInitialized = false;
        this.minDataForIndicators = 26; // Will be updated from backend
        
        console.log('📊 TradingChartManager initialized');
    }

    /**
     * Initialize the chart system
     */
    async initialize() {
        console.log('🚀 Starting chart initialization...');
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startChart());
        } else {
            this.startChart();
        }
    }

    /**
     * Start chart creation and data loading
     */
    startChart() {
        console.log('🎯 Starting chart system...');
        
        // Wait for Plotly to be available
        this.waitForPlotly().then(() => {
            this.createInitialChart();
            this.setupDataRefresh();
        }).catch(() => {
            this.createFallbackChart();
        });
    }

    /**
     * Wait for Plotly to load with timeout
     */
    waitForPlotly(timeout = 10000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const checkPlotly = () => {
                if (typeof Plotly !== 'undefined') {
                    console.log('✅ Plotly loaded successfully');
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    console.error('❌ Plotly failed to load within timeout');
                    reject();
                } else {
                    setTimeout(checkPlotly, 100);
                }
            };
            
            checkPlotly();
        });
    }

    /**
     * Create initial chart and load data
     */
    async createInitialChart() {
        const container = document.getElementById('priceChart');
        if (!container) {
            console.error('❌ Chart container not found');
            return;
        }

        // Load data and determine chart state
        await this.loadAllData();
        this.updateChart();
        this.chartInitialized = true;
    }

    /**
     * Load both market data and trades data
     */
    async loadAllData() {
        try {
            // Get minimum required data points from backend
            await this.loadMinRequiredData();
            
            // Load market data
            await this.loadMarketData();
            
            // Load trades data
            await this.loadTradesData();
            
        } catch (error) {
            console.log('📡 Error loading data:', error);
        }
    }

    /**
     * Get minimum required data points from backend configuration
     */
    async loadMinRequiredData() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/parameters`);
            if (response.ok) {
                const data = await response.json();
                if (data.derived_periods) {
                    this.minDataForIndicators = Math.max(
                        data.derived_periods.rsi_window,
                        data.derived_periods.macd_slow,
                        data.derived_periods.signal_window
                    );
                    console.log(`📊 Minimum data points required: ${this.minDataForIndicators}`);
                }
            }
        } catch (error) {
            console.log('Using default minimum data requirement:', this.minDataForIndicators);
        }
    }

    /**
     * Load market data from backend
     */
    async loadMarketData() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/market-data`);
            if (response.ok) {
                const result = await response.json();
                this.marketData = result.data || [];
                console.log(`📊 Loaded ${this.marketData.length} market data points`);
            } else {
                this.marketData = [];
            }
        } catch (error) {
            console.log('📊 Could not load market data from API');
            this.marketData = [];
        }
    }

    /**
     * Load trades data from backend
     */
    async loadTradesData() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/trades`);
            if (response.ok) {
                const result = await response.json();
                this.tradeData = result.trades || [];
                console.log(`📈 Loaded ${this.tradeData.length} trades`);
            } else {
                this.tradeData = [];
            }
        } catch (error) {
            console.log('📈 Could not load trades data from API');
            this.tradeData = [];
        }
    }

    /**
     * Update chart based on data availability
     */
    updateChart() {
        const container = document.getElementById('priceChart');
        if (!container) return;

        // Determine chart state based on data availability
        if (this.marketData.length === 0) {
            this.showNoDataState();
        } else if (this.marketData.length < this.minDataForIndicators) {
            this.showInsufficientDataState();
        } else {
            this.showFullTradingChart();
        }
    }

    /**
     * State 1: No price data available
     */
    showNoDataState() {
        console.log('📊 Showing no data state');
        
        const container = document.getElementById('priceChart');
        container.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 400px;
                background: rgba(15, 23, 42, 0.5);
                border: 2px dashed rgba(239, 68, 68, 0.4);
                border-radius: 12px;
                color: #e2e8f0;
                text-align: center;
                padding: 30px;
            ">
                <div style="font-size: 48px; margin-bottom: 20px;">📊</div>
                <div style="font-size: 20px; font-weight: 600; margin-bottom: 15px; color: #ef4444;">
                    No Price Data Available
                </div>
                <div style="font-size: 14px; color: #94a3b8; margin-bottom: 25px; line-height: 1.5;">
                    market_data.csv contains no price data<br>
                    Start the Python backend to begin collecting data
                </div>
            </div>
        `;
        
        this.showMessage('No price data found in market_data.csv', 'error');
    }

    /**
     * State 2: Some price data but not enough for indicators
     */
    showInsufficientDataState() {
        console.log(`📊 Showing insufficient data state: ${this.marketData.length}/${this.minDataForIndicators}`);
        
        if (typeof Plotly === 'undefined') {
            this.createFallbackChart();
            return;
        }

        // Create price-only chart
        const timestamps = this.marketData.map(d => new Date(d.datetime));
        const prices = this.marketData.map(d => d.price);

        const priceTrace = {
            x: timestamps,
            y: prices,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'BTC Price',
            line: { color: '#ff6b6b', width: 2 },
            marker: { color: '#ff6b6b', size: 4 }
        };

        const layout = {
            title: {
                text: `Bitcoin Price Data (${this.marketData.length}/${this.minDataForIndicators} for indicators)`,
                font: { color: '#e2e8f0' }
            },
            xaxis: { 
                title: 'Time', 
                color: '#e2e8f0',
                gridcolor: 'rgba(71, 85, 105, 0.3)',
                type: 'date'
            },
            yaxis: { 
                title: 'Price (USD)', 
                color: '#e2e8f0',
                gridcolor: 'rgba(71, 85, 105, 0.3)'
            },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(15, 23, 42, 0.3)',
            font: { color: '#e2e8f0' },
            margin: { t: 60, r: 30, b: 60, l: 70 },
            height: 400,
            annotations: [{
                text: `Collecting data for indicators (${this.marketData.length}/${this.minDataForIndicators})`,
                showarrow: false,
                x: 0.5,
                y: 0.95,
                xref: 'paper',
                yref: 'paper',
                font: { color: '#f59e0b', size: 12 }
            }]
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: true
        };

        Plotly.newPlot('priceChart', [priceTrace], layout, config)
            .then(() => {
                console.log('✅ Price-only chart created');
                this.showMessage(`Price data available but need ${this.minDataForIndicators - this.marketData.length} more data points for trading indicators`, 'warning');
            })
            .catch(error => {
                console.error('❌ Error creating price chart:', error);
                this.createFallbackChart();
            });
    }

    /**
     * State 3: Full data with indicators and trades
     */
    showFullTradingChart() {
        console.log(`📊 Showing full trading chart with ${this.marketData.length} data points and ${this.tradeData.length} trades`);
        
        if (typeof Plotly === 'undefined') {
            this.createFallbackChart();
            return;
        }

        const traces = [];

        // Price trace
        const timestamps = this.marketData.map(d => new Date(d.datetime));
        const prices = this.marketData.map(d => d.price);

        traces.push({
            x: timestamps,
            y: prices,
            type: 'scatter',
            mode: 'lines',
            name: 'BTC Price',
            line: { color: '#ff6b6b', width: 2 }
        });

        // Add trade markers if available
        if (this.tradeData.length > 0) {
            const buyTrades = this.tradeData.filter(t => t.side === 'BUY');
            const sellTrades = this.tradeData.filter(t => t.side === 'SELL');

            if (buyTrades.length > 0) {
                traces.push({
                    x: buyTrades.map(t => new Date(t.datetime)),
                    y: buyTrades.map(t => t.price),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Buy Orders',
                    marker: { color: '#10b981', size: 12, symbol: 'triangle-up' }
                });
            }

            if (sellTrades.length > 0) {
                traces.push({
                    x: sellTrades.map(t => new Date(t.datetime)),
                    y: sellTrades.map(t => t.price),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Sell Orders',
                    marker: { color: '#ef4444', size: 12, symbol: 'triangle-down' }
                });
            }
        }

        const layout = {
            title: {
                text: 'Bitcoin Trading Dashboard - Live Data',
                font: { color: '#e2e8f0' }
            },
            xaxis: { 
                title: 'Time', 
                color: '#e2e8f0',
                gridcolor: 'rgba(71, 85, 105, 0.3)',
                type: 'date'
            },
            yaxis: { 
                title: 'Price (USD)', 
                color: '#e2e8f0',
                gridcolor: 'rgba(71, 85, 105, 0.3)'
            },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(15, 23, 42, 0.3)',
            font: { color: '#e2e8f0' },
            legend: { font: { color: '#e2e8f0' } },
            margin: { t: 60, r: 30, b: 60, l: 70 },
            height: 400,
            showlegend: true
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: true
        };

        Plotly.newPlot('priceChart', traces, layout, config)
            .then(() => {
                console.log('✅ Full trading chart created');
                this.showMessage(`Trading chart active with ${this.marketData.length} data points and ${this.tradeData.length} trades`, 'success');
            })
            .catch(error => {
                console.error('❌ Error creating full chart:', error);
                this.createFallbackChart();
            });
    }

    /**
     * Create fallback chart when Plotly fails
     */
    createFallbackChart() {
        console.log('🔄 Creating fallback chart...');
        
        const container = document.getElementById('priceChart');
        if (!container) return;

        container.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 400px;
                background: rgba(15, 23, 42, 0.5);
                border: 2px dashed rgba(99, 102, 241, 0.4);
                border-radius: 12px;
                color: #e2e8f0;
                text-align: center;
                padding: 30px;
            ">
                <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
                <div style="font-size: 20px; font-weight: 600; margin-bottom: 15px;">
                    Chart Library Loading...
                </div>
                <div style="font-size: 14px; color: #94a3b8; margin-bottom: 25px; line-height: 1.5;">
                    Plotly.js is loading. Chart will appear when ready.<br>
                    Check your internet connection if this persists.
                </div>
            </div>
        `;
        
        this.showMessage('Chart library loading, please wait...', 'warning');
    }

    /**
     * Setup automatic data refresh
     */
    setupDataRefresh() {
        // Refresh data every 30 seconds
        setInterval(() => {
            if (this.chartInitialized) {
                this.refreshData();
            }
        }, 30000);
        
        console.log('🔄 Data refresh setup complete');
    }

    /**
     * Refresh data and update chart
     */
    async refreshData() {
        console.log('🔄 Refreshing chart data...');
        
        const previousDataLength = this.marketData.length;
        const previousTradesLength = this.tradeData.length;
        
        await this.loadAllData();
        
        // Only update chart if data changed
        if (this.marketData.length !== previousDataLength || 
            this.tradeData.length !== previousTradesLength) {
            console.log(`📊 Data updated: Market ${previousDataLength}→${this.marketData.length}, Trades ${previousTradesLength}→${this.tradeData.length}`);
            this.updateChart();
        }
    }

    /**
     * Show message in the visualization section
     */
    showMessage(text, type) {
        const messageDiv = document.getElementById('vizMessage');
        if (messageDiv) {
            messageDiv.textContent = text;
            messageDiv.className = `message ${type}`;
            messageDiv.style.display = 'block';
            
            if (type === 'success') {
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            }
        }
    }

    /**
     * Manual refresh method for external calls
     */
    async refresh() {
        console.log('🔄 Manual refresh triggered...');
        this.showMessage('Refreshing chart...', 'warning');
        
        await this.refreshData();
    }

    /**
     * Get debug information
     */
    getDebugInfo() {
        return {
            chartInitialized: this.chartInitialized,
            marketDataLength: this.marketData.length,
            tradeDataLength: this.tradeData.length,
            minDataForIndicators: this.minDataForIndicators,
            chartElementExists: !!document.getElementById('priceChart'),
            plotlyLoaded: typeof Plotly !== 'undefined',
            apiUrl: this.API_BASE_URL
        };
    }
}

// Global instance and initialization function
let chartManagerInstance = null;

window.initializeChartManager = function(apiBaseUrl = 'http://localhost:5000') {
    if (chartManagerInstance) {
        console.log('🔄 Reinitializing chart manager...');
    }
    
    chartManagerInstance = new TradingChartManager(apiBaseUrl);
    chartManagerInstance.initialize();
    return chartManagerInstance;
};

// Global refresh function for manual refresh
window.refreshChart = function() {
    if (chartManagerInstance) {
        chartManagerInstance.refresh();
    } else {
        console.warn('Chart manager not initialized');
    }
};

// Global debug function
window.debugChart = function() {
    if (chartManagerInstance) {
        const info = chartManagerInstance.getDebugInfo();
        console.log('=== CHART DEBUG INFO ===');
        console.table(info);
        return info;
    } else {
        console.warn('Chart manager not initialized');
        return null;
    }
};

console.log('🚀 Chart manager module loaded!');