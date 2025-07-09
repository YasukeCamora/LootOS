import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, origins='*')  # Simple CORS for now

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# API Configuration
COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY', '')
ETHEREUM_RPC_URL = os.environ.get('ETHEREUM_RPC_URL', '')
ONEINCH_API_KEY = os.environ.get('ONEINCH_API_KEY', '')

@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to LootOS - AI-Powered Crypto Trading Platform',
        'status': 'online',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'LootOS API',
        'message': 'All systems operational',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config')
def config_status():
    return jsonify({
        'database': 'configured' if os.environ.get('DATABASE_URL') else 'missing',
        'redis': 'configured' if os.environ.get('REDIS_URL') else 'missing',
        'ethereum_rpc': 'configured' if ETHEREUM_RPC_URL else 'missing',
        'coingecko_api': 'configured' if COINGECKO_API_KEY else 'missing',
        'oneinch_api': 'configured' if ONEINCH_API_KEY else 'missing'
    })

@app.route('/api/price/<token>')
def get_token_price(token):
    try:
        if not COINGECKO_API_KEY:
            return jsonify({'error': 'CoinGecko API key not configured', 'success': False}), 400
        
        token_map = {
            'eth': 'ethereum',
            'btc': 'bitcoin', 
            'ethereum': 'ethereum',
            'bitcoin': 'bitcoin',
            'cardano': 'cardano',
            'solana': 'solana'
        }
        
        token_id = token_map.get(token.lower(), token.lower())
        
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': token_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        headers = {'x-cg-demo-api-key': COINGECKO_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10 )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return jsonify({
                    'success': True,
                    'token': token,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No data found for token: {token}'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': f'CoinGecko API returned status {response.status_code}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Simple demo endpoints that match your frontend
@app.route('/api/portfolio')
def get_portfolio():
    return jsonify({
        'success': True,
        'portfolio': {
            'total_value': 15750.25,
            'daily_change': 2.34,
            'holdings': [
                {'token': 'ETH', 'amount': 5.5, 'value': 13475.75},
                {'token': 'BTC', 'amount': 0.05, 'value': 2162.50}
            ]
        }
    })

@app.route('/api/arbitrage')
def check_arbitrage():
    return jsonify({
        'success': True,
        'opportunities': [
            {
                'token_pair': 'ETH/USDC',
                'profit_potential': 0.21,
                'dex_1': 'Uniswap',
                'dex_2': 'SushiSwap'
            }
        ]
    })

@app.route('/api/gas-prices')
def get_gas_prices():
    return jsonify({
        'success': True,
        'gas_prices': {
            'fast': 25,
            'standard': 20,
            'safe': 15
        }
    })

@app.route('/api/agents')
def get_agents():
    return jsonify({
        'success': True,
        'agents': [
            {
                'name': 'Arbitrage Scanner',
                'status': 'active',
                'profit_24h': 45.67
            }
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
