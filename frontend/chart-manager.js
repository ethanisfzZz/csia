/**
 * Chart manager with authentication support
 */
class TradingChartManager {
    constructor(apiBaseUrl = 'http://localhost:5000') {
        this.marketData = [];
        this.tradeData = [];
        this.API_BASE_URL = apiBaseUrl;
        this.chartInitialized = false;
        this.minDataForIndicators = 26;
        
        console.log('📊 TradingChartManager initialized with auth');
    }

    /**
     * Get authentication headers
     */
    getAuthHeaders() {
        const token = sessionStorage.getItem('authToken');
        return {
            'Authorization': `Bearer ${token}`
        };
    }

    /**
     * Make authenticated API request
     */
    async authenticatedFetch(url) {
        const response = await fetch(url, {
            headers: this.getAuthHeaders()
        });
        
        if (response.status === 401) {
            console.log('🔐 Chart auth failed, redirecting...');
            sessionStorage.removeItem('authToken');
            window.location.href = 'login.html';
            throw new Error('Authentication failed');
        }
        
        return response;
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
        
        this.waitForPlotly().then(() => {
            this.createInitialChart();
            this.setupDataRefresh();
        }).catch(() => {
            this.createFallbackChart();
        });
    }

    /**
     * Wait for Plotly to load
     */
    waitForPlotly(timeout = 10000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const checkPlotly = () => {
                if (typeof Plotly !== 'undefined') {
                    console.log('✅ Plotly loaded successfully');
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    console.error('❌ Plotly failed to load');
                    reject();
                } else {
                    setTimeout(checkPlotly, 100);
                }
            };
            
            checkPlotly();
        });
    }

    /**
     * Create initial chart
     */
    async createInitialChart() {
        const container = document.getElementById('priceChart');
        if (!container) {
            console.error('❌ Chart container not found');
            return;
        }

        await this.loadAllData();
        this.updateChart();
        this.chartInitialized = true;
    }

    /**
     * Load all data
     */
    async loadAllData() {
        try {
            await this.loadMinRequiredData();
            await this.loadMarketData();
            await this.loadTradesData();
        } catch (error) {
            console.log('📡 Error loading chart data:', error);
        }
    }

    /**
     * Get minimum required data points
     */
    async loadMinRequiredData() {
        try {
            const response = await this.authenticatedFetch(`${this.API_BASE_URL}/parameters`);
            if (response.ok) {
                const data = await response.json();
                if (data.derived_periods) {
                    this.minDataForIndicators = Math.max(
                        data.derived_periods.rsi_window,
                        data.derived_periods.macd_slow,
                        data.derived_periods.signal_window
                    );
                    console.log(`📊 Min data points: ${this.minDataForIndicators}`);
                }
            }
        } catch (error) {
            console.log('📊 Using default min data:', this.minDataForIndicators);
        }
    }

    /**
     * Load market data
     */
    async loadMarketData() {
        try {
            const response = await this.authenticatedFetch(`${this.API_BASE_URL}/market-data`);
            if (response.ok) {
                const result = await response.json();
                this.marketData = result.data || [];
                console.log(`📊 Loaded ${this.marketData.length} market data points`);
            } else {
                this.marketData = [];
            }
        } catch (error) {
            console.log('📊 Could not load market data');
            this.marketData = [];
        }
    }

    /**
     * Load trades data
     */
    async loadTradesData() {
        try {
            const response = await this.authenticatedFetch(`${this.API_BASE_URL}/trades`);
            if (response.ok) {
                const result = await response.json();
                this.tradeData = result.trades || [];
                console.log(`📈 Loaded ${this.tradeData.length} trades`);
            } else {
                this.tradeData = [];
            }
        } catch (error) {
            console.log('📈 Could not load trades data');
            this.tradeData = [];
        }
    }

    /**
     * Update chart based on data availability
     */
    updateChart() {
        const container = document.getElementById('priceChart');
        if (!container) return;

        if (this.marketData.length === 0) {
            this.showNoDataState();
        } else if (this.marketData.length < this.minDataForIndicators) {
            this.showInsufficientDataState();
        } else {
            this.showFullTradingChart();
        }
    }

    /**
     * No data state
     */
    showNoDataState() {
        console.log('📊 No data available');
        
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
                <div style="font-size: 14px; color: #94a3b8; line-height: 1.5;">
                    Start the Python backend to begin collecting data
                </div>
            </div>
        `;
        
        this.showMessage('No price data found', 'error');
    }

    /**
     * Insufficient data state
     */
    showInsufficientDataState() {
        console.log(`📊 Insufficient data: ${this.marketData.length}/${this.minDataForIndicators}`);
        
        if (typeof Plotly === 'undefined') {
            this.createFallbackChart();
            return;
        }

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
            height: 400
        };

        Plotly.newPlot('priceChart', [priceTrace], layout, {
            responsive: true,
            displayModeBar: false,
            staticPlot: true
        })
        .then(() => {
            console.log('✅ Price chart created');
            this.showMessage(`Need ${this.minDataForIndicators - this.marketData.length} more data points for indicators`, 'warning');
        })
        .catch(error => {
            console.error('❌ Chart error:', error);
            this.createFallbackChart();
        });
    }

    /**
     * Full trading chart
     */
    showFullTradingChart() {
        console.log(`📊 Full chart: ${this.marketData.length} data, ${this.tradeData.length} trades`);
        
        if (typeof Plotly === 'undefined') {
            this.createFallbackChart();
            return;
        }

        const traces = [];
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

        Plotly.newPlot('priceChart', traces, layout, {
            responsive: true,
            displayModeBar: false,
            staticPlot: true
        })
        .then(() => {
            console.log('✅ Full trading chart created');
            this.showMessage(`Chart active: ${this.marketData.length} data points, ${this.tradeData.length} trades`, 'success');
        })
        .catch(error => {
            console.error('❌ Chart error:', error);
            this.createFallbackChart();
        });
    }

    /**
     * Fallback chart
     */
    createFallbackChart() {
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
                <div style="font-size: 14px; color: #94a3b8;">
                    Please wait for Plotly to load
                </div>
            </div>
        `;
    }

    /**
     * Setup data refresh
     */
    setupDataRefresh() {
        setInterval(() => {
            if (this.chartInitialized) {
                this.refreshData();
            }
        }, 30000);
        
        console.log('🔄 Chart refresh: every 30s');
    }

    /**
     * Refresh data
     */
    async refreshData() {
        console.log('🔄 Refreshing chart data...');
        
        const previousDataLength = this.marketData.length;
        const previousTradesLength = this.tradeData.length;
        
        await this.loadAllData();
        
        if (this.marketData.length !== previousDataLength || 
            this.tradeData.length !== previousTradesLength) {
            console.log(`📊 Chart data updated`);
            this.updateChart();
        }
    }

    /**
     * Show message
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
     * Manual refresh
     */
    async refresh() {
        console.log('🔄 Manual chart refresh...');
        this.showMessage('Refreshing chart...', 'warning');
        await this.refreshData();
    }
}

// Global functions
let chartManagerInstance = null;

window.initializeChartManager = function(apiBaseUrl = 'http://localhost:5000') {
    console.log('🎯 Initializing chart manager...');
    chartManagerInstance = new TradingChartManager(apiBaseUrl);
    chartManagerInstance.initialize();
    return chartManagerInstance;
};

window.refreshChart = function() {
    if (chartManagerInstance) {
        chartManagerInstance.refresh();
    } else {
        console.warn('Chart manager not initialized');
    }
};

console.log('🚀 Chart manager with authentication loaded!');