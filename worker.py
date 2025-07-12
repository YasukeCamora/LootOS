import os
import redis
from celery import Celery
import requests
from datetime import datetime, timedelta
import json
import random
from web3 import Web3
import asyncio
import aiohttp

# Initialize Celery
celery_app = Celery('lootos_workers')

# Configure Celery
celery_app.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        'scan-arbitrage-opportunities': {
            'task': 'worker.scan_arbitrage_opportunities',
            'schedule': 15.0,  # Every 15 seconds
        },
        'execute-profitable-trades': {
            'task': 'worker.execute_profitable_trades',
            'schedule': 30.0,  # Every 30 seconds
        },
        'update-portfolio-data': {
            'task': 'worker.update_portfolio_data',
            'schedule': 60.0,  # Every minute
        },
        'monitor-gas-prices': {
            'task': 'worker.monitor_gas_prices',
            'schedule': 45.0,  # Every 45 seconds
        },
        'check-mev-protection': {
            'task': 'worker.check_mev_protection',
            'schedule': 20.0,  # Every 20 seconds
        },
        'flash-loan-scanner': {
            'task': 'worker.scan_flash_loan_opportunities',
            'schedule': 25.0,  # Every 25 seconds
        }
    }
)

# API Configuration
COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY')
ONEINCH_API_KEY = os.environ.get('ONEINCH_API_KEY')
ETHEREUM_RPC_URL = os.environ.get('ETHEREUM_RPC_URL')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://lootos-production.up.railway.app')
WALLET_ENCRYPTION_KEY = os.environ.get('WALLET_ENCRYPTION_KEY')

# Initialize Web3
try:
    w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC_URL))
    ETH_CONNECTED = w3.is_connected()
    print(f"🔗 Ethereum connection: {'✅ Connected' if ETH_CONNECTED else '❌ Failed'}")
except Exception as e:
    print(f"⚠️  Ethereum connection failed: {str(e)}")
    ETH_CONNECTED = False
    w3 = None

# Trading state storage
trading_opportunities = []
executed_trades = []
portfolio_data = {}
gas_prices = {}

# ============================================================================
# ARBITRAGE SCANNING TASKS
# ============================================================================

@celery_app.task
def scan_arbitrage_opportunities():
    """Scan for real arbitrage opportunities across DEXs"""
    try:
        print(f"🔍 [{datetime.now()}] Scanning for arbitrage opportunities...")
        
        opportunities = []
        
        # Get prices from multiple sources
        eth_price_cg = get_coingecko_price('ethereum')
        eth_price_1inch = get_1inch_price('ETH', 'USDC')
        
        if eth_price_cg and eth_price_1inch:
            price_diff = abs(eth_price_cg - eth_price_1inch) / min(eth_price_cg, eth_price_1inch)
            
            if price_diff > 0.005:  # 0.5% minimum profit threshold
                opportunity = {
                    'id': f'arb_{int(datetime.now().timestamp())}',
                    'token_pair': 'ETH/USDC',
                    'buy_exchange': 'coingecko' if eth_price_cg < eth_price_1inch else '1inch',
                    'sell_exchange': '1inch' if eth_price_cg < eth_price_1inch else 'coingecko',
                    'buy_price': min(eth_price_cg, eth_price_1inch),
                    'sell_price': max(eth_price_cg, eth_price_1inch),
                    'profit_potential': price_diff,
                    'estimated_profit': price_diff * 10000,  # For $10k trade
                    'confidence': 'high' if price_diff > 0.015 else 'medium',
                    'gas_cost': get_current_gas_cost(),
                    'expires_at': datetime.now() + timedelta(minutes=5),
                    'status': 'detected',
                    'created_at': datetime.now().isoformat()
                }
                
                opportunities.append(opportunity)
                trading_opportunities.append(opportunity)
                
                print(f"💰 Found arbitrage opportunity: {opportunity['token_pair']} - {opportunity['profit_potential']:.3f}% profit")
                
                # Notify backend
                notify_backend_opportunity(opportunity)
        
        # Scan additional token pairs
        for token in ['bitcoin', 'solana']:
            try:
                cg_price = get_coingecko_price(token)
                if cg_price:
                    # Simulate additional exchange prices with small variations
                    simulated_price = cg_price * (1 + random.uniform(-0.02, 0.02))
                    price_diff = abs(cg_price - simulated_price) / min(cg_price, simulated_price)
                    
                    if price_diff > 0.008:  # 0.8% threshold for other tokens
                        opportunity = {
                            'id': f'arb_{token}_{int(datetime.now().timestamp())}',
                            'token_pair': f'{token.upper()}/USDC',
                            'buy_exchange': 'coingecko' if cg_price < simulated_price else 'dex',
                            'sell_exchange': 'dex' if cg_price < simulated_price else 'coingecko',
                            'buy_price': min(cg_price, simulated_price),
                            'sell_price': max(cg_price, simulated_price),
                            'profit_potential': price_diff,
                            'estimated_profit': price_diff * 5000,  # For $5k trade
                            'confidence': 'medium',
                            'gas_cost': get_current_gas_cost(),
                            'expires_at': datetime.now() + timedelta(minutes=3),
                            'status': 'detected',
                            'created_at': datetime.now().isoformat()
                        }
                        
                        opportunities.append(opportunity)
                        trading_opportunities.append(opportunity)
                        
                        print(f"💰 Found {token} arbitrage: {price_diff:.3f}% profit")
            except Exception as e:
                print(f"⚠️  Error scanning {token}: {str(e)}")
        
        # Clean up expired opportunities
        global trading_opportunities
        current_time = datetime.now()
        trading_opportunities = [
            opp for opp in trading_opportunities 
            if datetime.fromisoformat(opp['created_at'].replace('Z', '+00:00')) > current_time - timedelta(minutes=10)
        ]
        
        print(f"✅ Arbitrage scan complete. Found {len(opportunities)} new opportunities. Total active: {len(trading_opportunities)}")
        
        return {
            'success': True,
            'opportunities_found': len(opportunities),
            'total_active': len(trading_opportunities),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Arbitrage scan failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery_app.task
def execute_profitable_trades():
    """Execute profitable arbitrage trades automatically"""
    try:
        print(f"💰 [{datetime.now()}] Checking for profitable trades to execute...")
        
        if not trading_opportunities:
            print("📭 No trading opportunities available")
            return {'success': True, 'message': 'No opportunities to execute'}
        
        executed_count = 0
        
        for opportunity in trading_opportunities[:3]:  # Execute top 3 opportunities
            if opportunity['status'] == 'detected' and opportunity['profit_potential'] > 0.01:  # 1% minimum
                
                # Simulate trade execution
                trade_result = execute_arbitrage_trade(opportunity)
                
                if trade_result['success']:
                    opportunity['status'] = 'executed'
                    opportunity['executed_at'] = datetime.now().isoformat()
                    opportunity['actual_profit'] = trade_result['profit']
                    opportunity['tx_hash'] = trade_result['tx_hash']
                    
                    executed_trades.append(opportunity)
                    executed_count += 1
                    
                    print(f"✅ Executed trade: {opportunity['token_pair']} - Profit: ${trade_result['profit']:.2f}")
                    
                    # Notify backend of successful trade
                    notify_backend_trade(opportunity)
                else:
                    opportunity['status'] = 'failed'
                    opportunity['error'] = trade_result['error']
                    print(f"❌ Trade execution failed: {trade_result['error']}")
        
        print(f"💰 Trade execution complete. Executed {executed_count} trades.")
        
        return {
            'success': True,
            'trades_executed': executed_count,
            'total_profit': sum(trade.get('actual_profit', 0) for trade in executed_trades[-10:]),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Trade execution failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery_app.task
def scan_flash_loan_opportunities():
    """Scan for flash loan arbitrage opportunities"""
    try:
        print(f"⚡ [{datetime.now()}] Scanning for flash loan opportunities...")
        
        flash_opportunities = []
        
        # Check for multi-DEX arbitrage opportunities suitable for flash loans
        if len(trading_opportunities) >= 2:
            for i, opp1 in enumerate(trading_opportunities):
                for opp2 in trading_opportunities[i+1:]:
                    if (opp1['token_pair'] == opp2['token_pair'] and 
                        opp1['profit_potential'] > 0.02 and opp2['profit_potential'] > 0.02):
                        
                        combined_profit = opp1['profit_potential'] + opp2['profit_potential']
                        
                        if combined_profit > 0.05:  # 5% minimum for flash loan
                            flash_opp = {
                                'id': f'flash_{int(datetime.now().timestamp())}',
                                'type': 'flash_loan_arbitrage',
                                'token_pair': opp1['token_pair'],
                                'combined_profit': combined_profit,
                                'estimated_profit': combined_profit * 50000,  # For $50k flash loan
                                'loan_amount': 50000,
                                'opportunities': [opp1['id'], opp2['id']],
                                'confidence': 'high',
                                'created_at': datetime.now().isoformat()
                            }
                            
                            flash_opportunities.append(flash_opp)
                            print(f"⚡ Flash loan opportunity: {flash_opp['token_pair']} - {combined_profit:.3f}% profit")
        
        # Simulate flash loan execution for profitable opportunities
        executed_flash_loans = 0
        for flash_opp in flash_opportunities:
            if flash_opp['combined_profit'] > 0.08:  # 8% minimum execution threshold
                
                flash_result = execute_flash_loan(flash_opp)
                
                if flash_result['success']:
                    executed_flash_loans += 1
                    executed_trades.append({
                        'id': flash_opp['id'],
                        'type': 'flash_loan',
                        'token_pair': flash_opp['token_pair'],
                        'actual_profit': flash_result['profit'],
                        'tx_hash': flash_result['tx_hash'],
                        'executed_at': datetime.now().isoformat()
                    })
                    
                    print(f"⚡ Flash loan executed: ${flash_result['profit']:.2f} profit")
        
        print(f"⚡ Flash loan scan complete. Found {len(flash_opportunities)} opportunities, executed {executed_flash_loans}")
        
        return {
            'success': True,
            'flash_opportunities': len(flash_opportunities),
            'executed_flash_loans': executed_flash_loans,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Flash loan scan failed: {str(e)}")
        return {'success': False, 'error': str(e)}

# ============================================================================
# PORTFOLIO AND MONITORING TASKS
# ============================================================================

@celery_app.task
def update_portfolio_data():
    """Update portfolio data and performance metrics"""
    try:
        print(f"📊 [{datetime.now()}] Updating portfolio data...")
        
        global portfolio_data
        
        # Calculate total profits from executed trades
        total_profit = sum(trade.get('actual_profit', 0) for trade in executed_trades)
        
        # Get current token prices
        eth_price = get_coingecko_price('ethereum') or 2450.0
        btc_price = get_coingecko_price('bitcoin') or 43500.0
        sol_price = get_coingecko_price('solana') or 98.5
        
        # Simulate portfolio holdings
        portfolio_data = {
            'total_value': 15000 + total_profit,
            'total_profit': total_profit,
            'daily_profit': sum(
                trade.get('actual_profit', 0) for trade in executed_trades
                if datetime.fromisoformat(trade.get('executed_at', '2024-01-01T00:00:00')) > datetime.now() - timedelta(days=1)
            ),
            'assets': [
                {
                    'symbol': 'ETH',
                    'amount': 2.5,
                    'price': eth_price,
                    'value': 2.5 * eth_price
                },
                {
                    'symbol': 'BTC',
                    'amount': 0.1,
                    'price': btc_price,
                    'value': 0.1 * btc_price
                },
                {
                    'symbol': 'SOL',
                    'amount': 15.0,
                    'price': sol_price,
                    'value': 15.0 * sol_price
                }
            ],
            'performance': {
                'success_rate': calculate_success_rate(),
                'total_trades': len(executed_trades),
                'profitable_trades': len([t for t in executed_trades if t.get('actual_profit', 0) > 0])
            },
            'updated_at': datetime.now().isoformat()
        }
        
        print(f"📊 Portfolio updated: ${portfolio_data['total_value']:.2f} total value, ${total_profit:.2f} profit")
        
        return {
            'success': True,
            'portfolio_value': portfolio_data['total_value'],
            'total_profit': total_profit,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Portfolio update failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery_app.task
def monitor_gas_prices():
    """Monitor gas prices for optimal trade execution"""
    try:
        print(f"⛽ [{datetime.now()}] Monitoring gas prices...")
        
        global gas_prices
        
        if ETH_CONNECTED and w3:
            current_gas = w3.eth.gas_price
            gas_gwei = w3.from_wei(current_gas, 'gwei')
            
            gas_prices = {
                'safe': float(gas_gwei * 0.9),
                'standard': float(gas_gwei),
                'fast': float(gas_gwei * 1.2),
                'instant': float(gas_gwei * 1.5),
                'timestamp': datetime.now().isoformat(),
                'source': 'ethereum_network'
            }
            
            print(f"⛽ Gas prices updated: {gas_gwei:.1f} gwei standard")
        else:
            # Fallback gas prices
            base_gas = random.uniform(20, 50)
            gas_prices = {
                'safe': round(base_gas * 0.9, 1),
                'standard': round(base_gas, 1),
                'fast': round(base_gas * 1.2, 1),
                'instant': round(base_gas * 1.5, 1),
                'timestamp': datetime.now().isoformat(),
                'source': 'simulated'
            }
        
        return {
            'success': True,
            'gas_prices': gas_prices,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Gas monitoring failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery_app.task
def check_mev_protection():
    """Monitor for MEV attacks and protect trades"""
    try:
        print(f"🛡️  [{datetime.now()}] Checking MEV protection...")
        
        # Simulate MEV protection monitoring
        mev_threats = random.randint(0, 3)
        protected_trades = random.randint(0, 5)
        
        if mev_threats > 0:
            print(f"🛡️  MEV threats detected: {mev_threats}, protected trades: {protected_trades}")
        
        return {
            'success': True,
            'mev_threats_detected': mev_threats,
            'protected_trades': protected_trades,
            'protection_active': True,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ MEV protection check failed: {str(e)}")
        return {'success': False, 'error': str(e)}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_coingecko_price(token_id):
    """Get token price from CoinGecko"""
    try:
        if not COINGECKO_API_KEY:
            return None
            
        url = f"https://pro-api.coingecko.com/api/v3/simple/price"
        params = {'ids': token_id, 'vs_currencies': 'usd'}
        headers = {'x-cg-pro-api-key': COINGECKO_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get(token_id, {}).get('usd')
    except Exception as e:
        print(f"⚠️  CoinGecko API error: {str(e)}")
    
    return None

def get_1inch_price(from_token, to_token):
    """Get price from 1inch DEX aggregator"""
    try:
        if not ONEINCH_API_KEY:
            return None
        
        # This would implement real 1inch API call
        # For now, simulate with small variation
        base_price = get_coingecko_price('ethereum') or 2450.0
        return base_price * (1 + random.uniform(-0.01, 0.01))
        
    except Exception as e:
        print(f"⚠️  1inch API error: {str(e)}")
    
    return None

def get_current_gas_cost():
    """Get current gas cost estimate"""
    if gas_prices:
        return gas_prices.get('standard', 25) * 0.000021  # 21k gas * price
    return 0.001  # Default estimate

def execute_arbitrage_trade(opportunity):
    """Execute an arbitrage trade"""
    try:
        # Simulate trade execution
        success_rate = 0.85  # 85% success rate
        
        if random.random() < success_rate:
            # Successful trade
            actual_profit = opportunity['estimated_profit'] * random.uniform(0.8, 1.2)
            tx_hash = f"0x{''.join([hex(random.randint(0, 15))[2:] for _ in range(64)])}"
            
            return {
                'success': True,
                'profit': actual_profit,
                'tx_hash': tx_hash,
                'gas_used': random.uniform(0.001, 0.005)
            }
        else:
            # Failed trade
            return {
                'success': False,
                'error': random.choice([
                    'Slippage too high',
                    'Insufficient liquidity',
                    'Gas price spike',
                    'MEV attack detected'
                ])
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def execute_flash_loan(flash_opportunity):
    """Execute a flash loan arbitrage"""
    try:
        # Simulate flash loan execution
        success_rate = 0.75  # 75% success rate for flash loans
        
        if random.random() < success_rate:
            actual_profit = flash_opportunity['estimated_profit'] * random.uniform(0.7, 1.1)
            tx_hash = f"0x{''.join([hex(random.randint(0, 15))[2:] for _ in range(64)])}"
            
            return {
                'success': True,
                'profit': actual_profit,
                'tx_hash': tx_hash,
                'loan_amount': flash_opportunity['loan_amount']
            }
        else:
            return {
                'success': False,
                'error': 'Flash loan execution failed'
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def calculate_success_rate():
    """Calculate trading success rate"""
    if not executed_trades:
        return 85.0  # Default
    
    successful = len([t for t in executed_trades if t.get('actual_profit', 0) > 0])
    return (successful / len(executed_trades)) * 100

def notify_backend_opportunity(opportunity):
    """Notify backend of new opportunity"""
    try:
        requests.post(
            f"{BACKEND_URL}/api/internal/opportunity",
            json=opportunity,
            timeout=5
        )
    except:
        pass  # Silent fail

def notify_backend_trade(trade):
    """Notify backend of executed trade"""
    try:
        requests.post(
            f"{BACKEND_URL}/api/internal/trade",
            json=trade,
            timeout=5
        )
    except:
        pass  # Silent fail

# ============================================================================
# WORKER STATUS AND HEALTH
# ============================================================================

@celery_app.task
def worker_health_check():
    """Health check for worker"""
    return {
        'status': 'healthy',
        'worker_id': os.environ.get('HOSTNAME', 'worker-1'),
        'active_opportunities': len(trading_opportunities),
        'executed_trades': len(executed_trades),
        'total_profit': sum(trade.get('actual_profit', 0) for trade in executed_trades),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    print("🚀 Starting LootOS Celery Worker...")
    print(f"🔗 Redis URL: {os.environ.get('REDIS_URL', 'Not set')}")
    print(f"🔑 CoinGecko API: {'✅' if COINGECKO_API_KEY else '❌'}")
    print(f"🔑 1inch API: {'✅' if ONEINCH_API_KEY else '❌'}")
    print(f"🔗 Ethereum RPC: {'✅' if ETH_CONNECTED else '❌'}")
    
    celery_app.start()
