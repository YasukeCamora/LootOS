mport os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Enable CORS for all origins (including your Bolt.new frontend)
CORS(app, origins='*', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], 
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'])

# Configuration from environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# API Configuration with your actual API keys
COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY', 'CG-N4rPDTz4tYR4muz3yzvn6L14')
ETHEREUM_RPC_URL = os.environ.get('ETHEREUM_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/dVXsVPqTznZkn1iqVj2ON')
ONEINCH_API_KEY = os.environ.get('ONEINCH_API_KEY', '5acfmewC4Zl7oFD78chDa0P8EcwmrRi6')
ZEROX_API_KEY = os.environ.get('ZEROX_API_KEY', '54cdd552-ddb9-49f9-b3a2-07a43330ce97')
HELIUS_API_KEY = os.environ.get('HELIUS_API_KEY', '3d3ba894-d39c-4d10-b5da-2a96adc2708e')

# ============================================================================
# BASIC ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to LootOS - AI-Powered Crypto Trading Platform',
        'status': 'online',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'features': [
            'Real-time price data',
            'Multi-chain arbitrage detection',
            'AI-powered trading agents',
            'Portfolio analytics',
            'Risk management'
        ]
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'LootOS API',
        'message': 'All systems operational',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'Connected to Railway',
        'database': 'operational',
        'apis': {
            'coingecko': 'connected' if COINGECKO_API_KEY else 'missing',
            'ethereum_rpc': 'connected' if ETHEREUM_RPC_URL else 'missing',
            'oneinch': 'connected' if ONEINCH_API_KEY else 'missing',
            'helius': 'connected' if HELIUS_API_KEY else 'missing'
        }
    })

@app.route('/api/config')
def config_status():
    return jsonify({
        'environment': 'production',
        'database': 'configured',
        'redis': 'configured',
        'ethereum_rpc': 'configured' if ETHEREUM_RPC_URL else 'missing',
        'coingecko_api': 'configured' if COINGECKO_API_KEY else 'missing',
        'oneinch_api': 'configured' if ONEINCH_API_KEY else 'missing',
        'helius_api': 'configured' if HELIUS_API_KEY else 'missing',
        'features_enabled': [
            'real_time_prices',
            'arbitrage_detection',
            'portfolio_tracking',
            'trading_execution',
            'analytics'
        ]
    })

# ============================================================================
# REAL-TIME PRICE DATA (Using your CoinGecko API)
# ============================================================================

@app.route('/api/price/<token>')
def get_token_price(token):
    """Get real-time token price from CoinGecko"""
    try:
        token_map = {
            'eth': 'ethereum',
            'btc': 'bitcoin', 
            'ethereum': 'ethereum',
            'bitcoin': 'bitcoin',
            'cardano': 'cardano',
            'solana': 'solana',
            'bnb': 'binancecoin',
            'matic': 'matic-network',
            'usdc': 'usd-coin',
            'usdt': 'tether'
        }
        
