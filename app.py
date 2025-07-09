import os
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime

from flask_cors import CORS

app = Flask(__name__ )
CORS(app, 
     origins=[
         'https://chipper-toffee-d13f42.netlify.app',
         'https://zp1v56uxy8rdx5ypatb0ockcb9tr6a-oci3--5173--96435430.local-credentialless.webcontainer-api.io',
         'http://localhost:3000',
         'http://localhost:5173'
     ],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     supports_credentials=True )

methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
allow_headers=['Content-Type', 'Authorization'] )

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
        'timestamp': datetime.now().isoformat(),
        'features': [
            'Multi-chain trading',
            'Arbitrage detection', 
            'Flash loan integration',
            'Real-time analytics'
        ]
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
    """Check API configuration status"""
    return jsonify({
        'database': 'configured' if os.environ.get('DATABASE_URL') else 'missing',
        'redis': 'configured' if os.environ.get('REDIS_URL') else 'missing',
        'ethereum_rpc': 'configured' if ETHEREUM_RPC_URL else 'missing',
        'coingecko_api': 'configured' if COINGECKO_API_KEY else 'missing',
        'oneinch_api': 'configured' if ONEINCH_API_KEY else 'missing',
        'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'development')
    })

@app.route('/api/price/<token>')
def get_token_price(token):
    """Get token price from CoinGecko"""
    try:
        if not COINGECKO_API_KEY:
            return jsonify({'error': 'CoinGecko API key not configured', 'success': False}), 400
        
        # Map common token names
        token_map = {
            'eth': 'ethereum',
            'btc': 'bitcoin', 
            'ethereum': 'ethereum',
            'bitcoin': 'bitcoin',
            'cardano': 'cardano',
            'solana': 'solana'
        }
        
        token_id = token_map.get(token.lower(), token.lower())
        
        # Use demo API endpoint
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
                    'token_id': token_id,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No data found for token: {token}',
                    'suggestion': 'Try: ethereum, bitcoin, cardano, solana'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': f'CoinGecko API returned status {response.status_code}',
                'response': response.text[:200]
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'token': token
        }), 500

@app.route('/api/arbitrage')
def check_arbitrage():
    """Check for arbitrage opportunities"""
    try:
        opportunities = [
            {
                'token_pair': 'ETH/USDC',
                'dex_1': 'Uniswap',
                'dex_2': 'SushiSwap', 
                'price_1': 2450.50,
                'price_2': 2455.75,
                'profit_potential': 0.21,
                'gas_cost': 0.05,
                'net_profit': 0.16
            },
            {
                'token_pair': 'BTC/USDT',
                'dex_1': '1inch',
                'dex_2': 'Curve',
                'price_1': 43250.00,
                'price_2': 43275.50,
                'profit_potential': 0.06,
                'gas_cost': 0.03,
                'net_profit': 0.03
            }
        ]
        
        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'count': len(opportunities),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/gas-prices')
def get_gas_prices():
    """Get current gas prices"""
    try:
        # Fallback gas prices for demo
        return jsonify({
            'success': True,
            'gas_prices': {
                'fast': 25,
                'standard': 20,
                'safe': 15
            },
            'note': 'Demo gas prices',
            'timestamp': datetime.now().isoformat()
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio data"""
    try:
        portfolio = {
            'total_value': 15750.25,
            'daily_change': 2.34,
            'daily_change_percent': 0.15,
            'holdings': [
                {
                    'token': 'ETH',
                    'amount': 5.5,
                    'value': 13475.75,
                    'change_24h': 1.8
                },
                {
                    'token': 'BTC', 
                    'amount': 0.05,
                    'value': 2162.50,
                    'change_24h': 0.5
                },
                {
                    'token': 'USDC',
                    'amount': 112.00,
                    'value': 112.00,
                    'change_24h': 0.0
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agents')
def get_agents():
    """Get AI agent status"""
    try:
        agents = [
            {
                'id': 'arbitrage_bot_1',
                'name': 'Arbitrage Scanner',
                'status': 'active',
                'profit_24h': 45.67,
                'trades_24h': 12,
                'success_rate': 85.5
            },
            {
                'id': 'flash_loan_bot_1', 
                'name': 'Flash Loan Exploiter',
                'status': 'active',
                'profit_24h': 123.45,
                'trades_24h': 3,
                'success_rate': 100.0
            },
            {
                'id': 'honeypot_scanner_1',
                'name': 'Honeypot Scanner',
                'status': 'monitoring',
                'profit_24h': 0.00,
                'trades_24h': 0,
                'success_rate': 95.2
            }
        ]
        
        return jsonify({
            'success': True,
            'agents': agents,
            'total_profit_24h': sum(agent['profit_24h'] for agent in agents),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@app.route('/api/dashboard-analytics')
def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        analytics = {
            'total_profit': 1247.89,
            'daily_profit': 89.45,
            'weekly_profit': 456.78,
            'monthly_profit': 1247.89,
            'profit_change_24h': 12.5,
            'active_trades': 7,
            'successful_trades': 156,
            'total_trades': 189,
            'success_rate': 82.5,
            'portfolio_value': 15750.25,
            'portfolio_change_24h': 2.34,
            'top_performing_token': {
                'symbol': 'ETH',
                'profit': 234.56,
                'change_24h': 5.8
            },
            'recent_trades': [
                {
                    'id': 'trade_001',
                    'type': 'arbitrage',
                    'token_pair': 'ETH/USDC',
                    'profit': 45.67,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'id': 'trade_002', 
                    'type': 'flash_loan',
                    'token_pair': 'BTC/USDT',
                    'profit': 123.45,
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio-overview')
def get_portfolio_overview():
    """Get portfolio overview data"""
    try:
        overview = {
            'total_value': 15750.25,
            'daily_change': 234.56,
            'daily_change_percent': 1.52,
            'weekly_change': 1247.89,
            'weekly_change_percent': 8.6,
            'monthly_change': 2456.78,
            'monthly_change_percent': 18.5,
            'asset_allocation': [
                {
                    'symbol': 'ETH',
                    'name': 'Ethereum',
                    'amount': 5.5,
                    'value': 13475.75,
                    'percentage': 85.5,
                    'change_24h': 1.8
                },
                {
                    'symbol': 'BTC',
                    'name': 'Bitcoin', 
                    'amount': 0.05,
                    'value': 2162.50,
                    'percentage': 13.7,
                    'change_24h': 0.5
                },
                {
                    'symbol': 'USDC',
                    'name': 'USD Coin',
                    'amount': 112.00,
                    'value': 112.00,
                    'percentage': 0.7,
                    'change_24h': 0.0
                }
            ],
            'performance_metrics': {
                'sharpe_ratio': 1.85,
                'max_drawdown': -5.2,
                'volatility': 12.8,
                'beta': 0.95
            }
        }
        
        return jsonify({
            'success': True,
            'overview': overview,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/connect', methods=['POST'])
def connect_wallet():
    """Handle wallet connection"""
    try:
        data = request.get_json()
        wallet_type = data.get('type', '')
        address = data.get('address', '')
        
        if not wallet_type or not address:
            return jsonify({
                'success': False,
                'error': 'Wallet type and address required'
            }), 400
        
        # Simulate wallet connection
        wallet_info = {
            'type': wallet_type,
            'address': address,
            'connected': True,
            'balance': {
                'ETH': 5.5,
                'BTC': 0.05,
                'USDC': 112.00
            },
            'network': 'mainnet' if wallet_type == 'metamask' else 'solana-mainnet'
        }
        
        return jsonify({
            'success': True,
            'wallet': wallet_info,
            'message': f'{wallet_type.title()} wallet connected successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/disconnect', methods=['POST'])
def disconnect_wallet():
    """Handle wallet disconnection"""
    try:
        return jsonify({
            'success': True,
            'message': 'Wallet disconnected successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/balance/<address>')
def get_wallet_balance(address):
    """Get wallet balance for address"""
    try:
        # Simulate balance check
        balance = {
            'address': address,
            'balances': [
                {
                    'token': 'ETH',
                    'symbol': 'ETH',
                    'amount': 5.5,
                    'value_usd': 13475.75
                },
                {
                    'token': 'BTC',
                    'symbol': 'BTC', 
                    'amount': 0.05,
                    'value_usd': 2162.50
                },
                {
                    'token': 'USDC',
                    'symbol': 'USDC',
                    'amount': 112.00,
                    'value_usd': 112.00
                }
            ],
            'total_value_usd': 15750.25
        }
        
        return jsonify({
            'success': True,
            'balance': balance,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
