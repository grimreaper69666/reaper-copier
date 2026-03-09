#!/usr/bin/env python3
"""
REAPER TRADE COPIER v3.0
Modular broker system - add any broker you want
"""

from flask import Flask, request, abort, jsonify, render_template_string
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Type
from abc import ABC, abstractmethod
import requests
import os
from dataclasses import dataclass, asdict
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trades.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== CONFIGURATION ==========
class Config:
    """All settings in one place"""
    
    # Core
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'change-this-key')
    SERVER_PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ACTIVE_BROKER = os.getenv('ACTIVE_BROKER', 'tradovate')
    
    # Account
    ACCOUNT_SIZE = float(os.getenv('ACCOUNT_SIZE', 10000))
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 0.02))
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 5))
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', 0.05))
    
    # Sizing modes: fixed, percent, risk, kelly
    SIZING_MODE = os.getenv('SIZING_MODE', 'risk')
    FIXED_QUANTITY = int(os.getenv('FIXED_QUANTITY', 1))
    PERCENT_PER_TRADE = float(os.getenv('PERCENT_PER_TRADE', 0.10))
    
    # Orders
    USE_BRACKET_ORDERS = os.getenv('USE_BRACKET_ORDERS', 'True').lower() == 'true'
    DEFAULT_ORDER_TYPE = os.getenv('DEFAULT_ORDER_TYPE', 'Market')
    MIN_RISK_REWARD = float(os.getenv('MIN_RISK_REWARD', 1.5))
    
    # Time
    MAX_TRADES_PER_HOUR = int(os.getenv('MAX_TRADES_PER_HOUR', 10))
    COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', 0))
    
    # Notifications
    DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Tradovate
    TRADOVATE_USERNAME = os.getenv('TRADOVATE_USERNAME', '')
    TRADOVATE_PASSWORD = os.getenv('TRADOVATE_PASSWORD', '')
    TRADOVATE_ACCOUNT_ID = os.getenv('TRADOVATE_ACCOUNT_ID', '')
    TRADOVATE_DEMO = os.getenv('TRADOVATE_DEMO', 'True').lower() == 'true'
    
    # TradeStation
    TRADESTATION_API_KEY = os.getenv('TRADESTATION_API_KEY', '')
    TRADESTATION_API_SECRET = os.getenv('TRADESTATION_API_SECRET', '')
    TRADESTATION_ACCOUNT_ID = os.getenv('TRADESTATION_ACCOUNT_ID', '')
    TRADESTATION_REFRESH_TOKEN = os.getenv('TRADESTATION_REFRESH_TOKEN', '')
    TRADESTATION_DEMO = os.getenv('TRADESTATION_DEMO', 'True').lower() == 'true'

config = Config()

# ========== BASE BROKER CLASS ==========
class BaseBroker(ABC):
    """Abstract base class - all brokers must implement this"""
    
    name: str = "base"
    supports_bracket_orders: bool = False
    supports_native_stops: bool = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with broker. Return True on success."""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int,
                    order_type: str = 'Market', stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None, **kwargs) -> Dict:
        """Place an order. Return dict with 'status' and 'data' or 'message'."""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """Get current positions. Return list of position dicts."""
        pass
    
    @abstractmethod
    def get_orders(self) -> List[Dict]:
        """Get open orders. Return list of order dicts."""
        pass
    
    def close(self):
        """Cleanup resources. Override if needed."""
        pass


# ========== TRADOVATE IMPLEMENTATION ==========
class TradovateBroker(BaseBroker):
    """Tradovate futures broker"""
    
    name = "tradovate"
    supports_bracket_orders = True
    supports_native_stops = True
    
    BASE_URL = 'https://live.tradovateapi.com/v1'
    DEMO_URL = 'https://demo.tradovateapi.com/v1'
    
    def __init__(self, username: str, password: str, account_id: str, demo: bool = True):
        self.username = username
        self.password = password
        self.account_id = account_id
        self.demo = demo
        self.base_url = self.DEMO_URL if demo else self.BASE_URL
        self.access_token = None
        self.token_expires = None
    
    def authenticate(self) -> bool:
        try:
            auth_data = {
                'name': self.username,
                'password': self.password,
                'appId': 'ReaperCopier',
                'appVersion': '3.0',
                'deviceId': 'reaper-device'
            }
            
            response = requests.post(
                f"{self.base_url}/auth/accesstokenrequest",
                json=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')
                expires = data.get('expirationTime', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires)
                logger.info("Tradovate: Authenticated")
                return True
            else:
                logger.error(f"Tradovate auth failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Tradovate auth error: {e}")
            return False
    
    def _headers(self) -> Dict:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _check_auth(self):
        if not self.access_token or (self.token_expires and datetime.now() > self.token_expires - timedelta(minutes=5)):
            self.authenticate()
    
    def place_order(self, symbol: str, side: str, quantity: int,
                    order_type: str = 'Market', stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None, **kwargs) -> Dict:
        
        self._check_auth()
        
        action = 'Buy' if side == 'LONG' else 'Sell'
        
        order_spec = {
            'accountSpec': self.account_id,
            'action': action,
            'symbol': symbol,
            'orderQty': quantity,
            'orderType': order_type,
            'timeInForce': 'Day'
        }
        
        if order_type == 'Limit' and 'price' in kwargs:
            order_spec['price'] = kwargs['price']
        
        # Bracket orders (entry + stop + target in one call)
        if config.USE_BRACKET_ORDERS and (stop_loss or take_profit):
            bracket = {}
            if stop_loss:
                bracket['stopLoss'] = stop_loss
            if take_profit:
                bracket['profitTarget'] = take_profit
            if bracket:
                order_spec['bracket'] = bracket
        
        try:
            response = requests.post(
                f"{self.base_url}/order/placeorder",
                json=order_spec,
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {'status': 'success', 'data': result}
            else:
                return {'status': 'error', 'message': response.text}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_positions(self) -> List[Dict]:
        self._check_auth()
        try:
            response = requests.get(f"{self.base_url}/position/list", headers=self._headers(), timeout=10)
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def get_orders(self) -> List[Dict]:
        self._check_auth()
        try:
            response = requests.get(f"{self.base_url}/order/list", headers=self._headers(), timeout=10)
            return response.json() if response.status_code == 200 else []
        except:
            return []


# ========== TRADESTATION IMPLEMENTATION ==========
class TradeStationBroker(BaseBroker):
    """TradeStation futures broker"""
    
    name = "tradestation"
    supports_bracket_orders = False
    supports_native_stops = True
    
    BASE_URL = 'https://api.tradestation.com/v3'
    
    def __init__(self, api_key: str, api_secret: str, account_id: str, 
                 refresh_token: str = '', demo: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_id = account_id
        self.refresh_token = refresh_token
        self.demo = demo
        self.access_token = None
        self.token_expires = None
    
    def authenticate(self) -> bool:
        try:
            if not self.refresh_token:
                logger.error("TradeStation: Need refresh_token for OAuth")
                return False
            
            auth_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.api_key,
                'client_secret': self.api_secret
            }
            
            response = requests.post(
                f"{self.BASE_URL}/security/authorize",
                data=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                expires = data.get('expires_in', 1200)
                self.token_expires = datetime.now() + timedelta(seconds=expires)
                logger.info("TradeStation: Authenticated")
                return True
            else:
                logger.error(f"TradeStation auth failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"TradeStation auth error: {e}")
            return False
    
    def _headers(self) -> Dict:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _check_auth(self):
        if not self.access_token or (self.token_expires and datetime.now() > self.token_expires - timedelta(minutes=5)):
            self.authenticate()
    
    def place_order(self, symbol: str, side: str, quantity: int,
                    order_type: str = 'Market', stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None, **kwargs) -> Dict:
        
        self._check_auth()
        
        action = 'BUY' if side == 'LONG' else 'SELL'
        
        order_data = {
            'AccountID': self.account_id,
            'Symbol': symbol,
            'Quantity': str(quantity),
            'OrderType': order_type,
            'TradeAction': action,
            'TimeInForce': 'Day'
        }
        
        if order_type == 'Limit' and 'price' in kwargs:
            order_data['LimitPrice'] = str(kwargs['price'])
        
        if stop_loss:
            order_data['StopLoss'] = str(stop_loss)
        if take_profit:
            order_data['TakeProfit'] = str(take_profit)
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/orders",
                json=order_data,
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return {'status': 'success', 'data': response.json()}
            else:
                return {'status': 'error', 'message': response.text}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_positions(self) -> List[Dict]:
        self._check_auth()
        try:
            url = f"{self.BASE_URL}/brokerage/accounts/{self.account_id}/positions"
            response = requests.get(url, headers=self._headers(), timeout=10)
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def get_orders(self) -> List[Dict]:
        self._check_auth()
        try:
            url = f"{self.BASE_URL}/brokerage/accounts/{self.account_id}/orders"
            response = requests.get(url, headers=self._headers(), timeout=10)
            return response.json() if response.status_code == 200 else []
        except:
            return []


# ========== BROKER REGISTRY ==========
class BrokerRegistry:
    """Registry pattern - add any broker you want"""
    
    _brokers: Dict[str, Type[BaseBroker]] = {}
    _instances: Dict[str, BaseBroker] = {}
    
    @classmethod
    def register(cls, name: str, broker_class: Type[BaseBroker]):
        """Register a new broker class"""
        cls._brokers[name] = broker_class
        logger.info(f"Registered broker: {name}")
    
    @classmethod
    def get_broker_class(cls, name: str) -> Optional[Type[BaseBroker]]:
        """Get broker class by name"""
        return cls._brokers.get(name)
    
    @classmethod
    def create_broker(cls, name: str, **kwargs) -> Optional[BaseBroker]:
        """Create broker instance"""
        broker_class = cls.get_broker_class(name)
        if broker_class:
            instance = broker_class(**kwargs)
            cls._instances[name] = instance
            return instance
        return None
    
    @classmethod
    def get_broker(cls, name: str) -> Optional[BaseBroker]:
        """Get existing broker instance"""
        return cls._instances.get(name)
    
    @classmethod
    def list_brokers(cls) -> List[str]:
        """List all registered broker names"""
        return list(cls._brokers.keys())
    
    @classmethod
    def init_default_brokers(cls):
        """Initialize default brokers (Tradovate, TradeStation)"""
        # Register default brokers
        cls.register('tradovate', TradovateBroker)
        cls.register('tradestation', TradeStationBroker)
        
        # Create instances if configured
        if config.TRADOVATE_USERNAME and config.TRADOVATE_PASSWORD:
            cls.create_broker(
                'tradovate',
                username=config.TRADOVATE_USERNAME,
                password=config.TRADOVATE_PASSWORD,
                account_id=config.TRADOVATE_ACCOUNT_ID,
                demo=config.TRADOVATE_DEMO
            )
        
        if config.TRADESTATION_API_KEY and config.TRADESTATION_API_SECRET:
            cls.create_broker(
                'tradestation',
                api_key=config.TRADESTATION_API_KEY,
                api_secret=config.TRADESTATION_API_SECRET,
                account_id=config.TRADESTATION_ACCOUNT_ID,
                refresh_token=config.TRADESTATION_REFRESH_TOKEN,
                demo=config.TRADESTATION_DEMO
            )

# Initialize registry
BrokerRegistry.init_default_brokers()


# ========== TRADE MODELS & MANAGER ==========
@dataclass
class Trade:
    id: str
    symbol: str
    side: str
    quantity: int
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    strategy: str
    timestamp: datetime
    status: str = 'open'
    exit_price: Optional[float] = None
    pnl: float = 0.0
    broker: str = ''
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class TradeManager:
    """Manages all trading operations"""
    
    def __init__(self):
        self.positions: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_trades = 0
        self.last_trade_time = datetime.min
        self.trades_this_hour = 0
        self.hour_start = datetime.now()
        self._lock = threading.Lock()
    
    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed"""
        now = datetime.now()
        
        # Cooldown
        if config.COOLDOWN_MINUTES > 0:
            minutes_since = (now - self.last_trade_time).total_seconds() / 60
            if minutes_since < config.COOLDOWN_MINUTES:
                remaining = config.COOLDOWN_MINUTES - minutes_since
                return False, f"Cooldown: {remaining:.1f} min"
        
        # Hourly limit
        if now.hour != self.hour_start.hour:
            self.trades_this_hour = 0
            self.hour_start = now
        
        if self.trades_this_hour >= config.MAX_TRADES_PER_HOUR:
            return False, f"Max {config.MAX_TRADES_PER_HOUR} trades/hour"
        
        # Daily loss
        if self.daily_pnl < -config.ACCOUNT_SIZE * config.MAX_DAILY_LOSS:
            return False, "Daily loss limit"
        
        # Max positions
        if len(self.positions) >= config.MAX_POSITIONS:
            return False, f"Max {config.MAX_POSITIONS} positions"
        
        return True, "OK"
    
    def calculate_size(self, entry: float, stop: float, symbol: str = '') -> int:
        """Calculate position size"""
        
        if config.SIZING_MODE == 'fixed':
            return config.FIXED_QUANTITY
        
        elif config.SIZING_MODE == 'percent':
            position_value = config.ACCOUNT_SIZE * config.PERCENT_PER_TRADE
            contract_value = entry * 20 if 'NQ' in symbol else entry * 50
            return max(1, int(position_value / contract_value))
        
        elif config.SIZING_MODE == 'risk':
            if not stop or stop == 0:
                return config.FIXED_QUANTITY
            
            risk_amount = config.ACCOUNT_SIZE * config.RISK_PER_TRADE
            risk_per_contract = abs(entry - stop)
            point_value = 20 if 'NQ' in symbol else 50
            risk_per_contract *= point_value
            
            if risk_per_contract == 0:
                return config.FIXED_QUANTITY
            
            return max(1, int(risk_amount / risk_per_contract))
        
        elif config.SIZING_MODE == 'kelly':
            win_rate = 0.55
            avg_win = abs(entry - stop) * 2 if stop else entry * 0.01
            avg_loss = abs(entry - stop) if stop else entry * 0.005
            
            if avg_loss == 0:
                return config.FIXED_QUANTITY
            
            kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly = max(0, min(kelly, 0.25))
            
            risk_amount = config.ACCOUNT_SIZE * kelly
            risk_per_contract = abs(entry - stop) * (20 if 'NQ' in symbol else 50)
            
            if risk_per_contract == 0:
                return config.FIXED_QUANTITY
            
            return max(1, int(risk_amount / risk_per_contract))
        
        return config.FIXED_QUANTITY
    
    def add_trade(self, trade: Trade) -> bool:
        with self._lock:
            if trade.symbol in self.positions:
                logger.warning(f"Already in {trade.symbol}")
                return False
            
            self.positions[trade.symbol] = trade
            self.daily_trades += 1
            self.total_trades += 1
            self.trades_this_hour += 1
            self.last_trade_time = datetime.now()
            
            logger.info(f"Trade: {trade.side} {trade.quantity} {trade.symbol} @ {trade.entry_price}")
            return True
    
    def close_trade(self, symbol: str, exit_price: float) -> Optional[Trade]:
        with self._lock:
            if symbol not in self.positions:
                return None
            
            trade = self.positions[symbol]
            trade.exit_price = exit_price
            trade.status = 'closed'
            
            if trade.side == 'LONG':
                trade.pnl = (exit_price - trade.entry_price) * trade.quantity
            else:
                trade.pnl = (trade.entry_price - exit_price) * trade.quantity
            
            point_value = 20 if 'NQ' in symbol else 50
            trade.pnl *= point_value
            
            self.daily_pnl += trade.pnl
            self.closed_trades.append(trade)
            del self.positions[symbol]
            
            logger.info(f"Closed: {symbol} P&L: ${trade.pnl:.2f}")
            return trade
    
    def get_stats(self) -> Dict:
        total_pnl = sum(t.pnl for t in self.closed_trades)
        winners = [t for t in self.closed_trades if t.pnl > 0]
        losers = [t for t in self.closed_trades if t.pnl <= 0]
        
        return {
            'total_trades': self.total_trades,
            'open_positions': len(self.positions),
            'daily_pnl': self.daily_pnl,
            'total_pnl': total_pnl,
            'win_rate': len(winners) / len(self.closed_trades) if self.closed_trades else 0,
            'avg_win': sum(t.pnl for t in winners) / len(winners) if winners else 0,
            'avg_loss': sum(t.pnl for t in losers) / len(losers) if losers else 0,
        }

trade_manager = TradeManager()


# ========== NOTIFICATIONS ==========
class NotificationManager:
    def __init__(self):
        self.channels = []
        if config.DISCORD_WEBHOOK:
            self.channels.append('discord')
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            self.channels.append('telegram')
    
    def notify(self, title: str, message: str):
        for channel in self.channels:
            try:
                if channel == 'discord':
                    requests.post(config.DISCORD_WEBHOOK, json={'content': f'**{title}**\n{message}'}, timeout=5)
                elif channel == 'telegram':
                    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
                    requests.post(url, json={'chat_id': config.TELEGRAM_CHAT_ID, 'text': f"*{title}*\n{message}", 'parse_mode': 'Markdown'}, timeout=5)
            except Exception as e:
                logger.error(f"Notify error: {e}")

notification_manager = NotificationManager()


# ========== WEB ROUTES ==========
@app.route('/')

@app.route('/')
def dashboard():
    '''Serve the management UI'''
    try:
        with open('static/index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'UI not found'}), 500

def webhook():
    """TradingView webhook"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data'}), 400
        
        if data.get('secret') != config.WEBHOOK_SECRET:
            return jsonify({'status': 'error', 'message': 'Invalid secret'}), 403
        
        symbol = data.get('symbol', 'MNQ')
        side = data.get('side', 'LONG').upper()
        entry = float(data.get('price', 0))
        stop = float(data['stop_loss']) if data.get('stop_loss') else None
        target = float(data['take_profit']) if data.get('take_profit') else None
        strategy = data.get('strategy', 'default')
        
        # Check constraints
        can_trade, reason = trade_manager.can_trade()
        if not can_trade:
            return jsonify({'status': 'rejected', 'reason': reason}), 200
        
        # Check R:R
        if stop and target:
            risk = abs(entry - stop)
            reward = abs(target - entry)
            if risk > 0 and reward / risk < config.MIN_RISK_REWARD:
                return jsonify({'status': 'rejected', 'reason': 'Low R:R'}), 200
        
        # Calculate size
        quantity = trade_manager.calculate_size(entry, stop, symbol)
        
        # Get broker
        broker = BrokerRegistry.get_broker(config.ACTIVE_BROKER)
        if not broker:
            return jsonify({'status': 'error', 'message': f'Broker {config.ACTIVE_BROKER} not configured'}), 500
        
        # Place order
        result = broker.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            stop_loss=stop,
            take_profit=target
        )
        
        if result['status'] == 'success':
            trade = Trade(
                id=result['data'].get('orderId', str(datetime.now().timestamp())),
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry,
                stop_loss=stop,
                take_profit=target,
                strategy=strategy,
                timestamp=datetime.now(),
                broker=config.ACTIVE_BROKER
            )
            
            trade_manager.add_trade(trade)
            notification_manager.notify(f"New {side} Position", f"{symbol} @ {entry}")
            
            return jsonify({
                'status': 'success',
                'broker': config.ACTIVE_BROKER,
                'trade': trade.to_dict()
            }), 200
        else:
            return jsonify({'status': 'error', 'message': result.get('message')}), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/status')
def status():
    """API status"""
    brokers = BrokerRegistry.list_brokers()
    available = [b for b in brokers if BrokerRegistry.get_broker(b)]
    
    return jsonify({
        'status': 'online',
        'active_broker': config.ACTIVE_BROKER,
        'available_brokers': available,
        'all_brokers': brokers,
        'stats': trade_manager.get_stats(),
        'config': {
            'sizing_mode': config.SIZING_MODE,
            'risk_per_trade': config.RISK_PER_TRADE,
            'max_positions': config.MAX_POSITIONS
        }
    })


@app.route('/brokers')
def list_brokers():
    """List all registered brokers"""
    return jsonify({
        'registered': BrokerRegistry.list_brokers(),
        'configured': [b for b in BrokerRegistry.list_brokers() if BrokerRegistry.get_broker(b)],
        'active': config.ACTIVE_BROKER
    })


# ========== ADD CUSTOM BROKERS HERE ==========
"""
EXAMPLE: How to add a new broker

1. Create a new class that inherits from BaseBroker:

class InteractiveBrokers(BaseBroker):
    name = "interactivebrokers"
    supports_bracket_orders = True
    
    def __init__(self, host: str, port: int, client_id: int):
        self.host = host
        self.port = port
        self.client_id = client_id
        # ... IB connection setup
    
    def authenticate(self) -> bool:
        # Connect to TWS/Gateway
        return True
    
    def place_order(self, symbol, side, quantity, **kwargs):
        # Implement IB order placement
        return {'status': 'success', 'data': {...}}
    
    def get_positions(self) -> List[Dict]:
        # Return IB positions
        return []
    
    def get_orders(self) -> List[Dict]:
        # Return IB orders
        return []

2. Register the broker:

BrokerRegistry.register('interactivebrokers', InteractiveBrokers)
BrokerRegistry.create_broker('interactivebrokers', host='127.0.0.1', port=7497, client_id=1)

3. Use it:

export ACTIVE_BROKER=interactivebrokers
python trade_copier.py
"""


@app.route('/brokers/available')
def available_brokers():
    """List all registered brokers and their status"""
    brokers = BrokerRegistry.list_brokers()
    available = [b for b in brokers if BrokerRegistry.get_broker(b)]
    
    return jsonify({
        'registered': brokers,
        'configured': available,
        'active': config.ACTIVE_BROKER
    })


@app.route('/configure/broker', methods=['POST'])
def configure_broker():
    """Configure broker credentials from dashboard"""
    try:
        data = request.get_json()
        broker_type = data.get('broker_type', 'tradovate')
        
        if broker_type == 'tradovate':
            username = data.get('username')
            password = data.get('password')
            account_id = data.get('account_id')
            demo = data.get('demo', True)
            
            if not username or not password:
                return jsonify({'status': 'error', 'message': 'Username and password required'}), 400
            
            # Create and register Tradovate broker
            broker = TradovateBroker(
                username=username,
                password=password,
                account_id=account_id,
                demo=demo
            )
            
            # Test authentication
            if broker.authenticate():
                BrokerRegistry._instances['tradovate'] = broker
                config.ACTIVE_BROKER = 'tradovate'
                logger.info(f"Tradovate configured for user: {username}")
                return jsonify({'status': 'success', 'message': 'Tradovate connected'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Authentication failed'}), 401
                
        elif broker_type == 'tradestation':
            api_key = data.get('api_key')
            api_secret = data.get('api_secret')
            account_id = data.get('account_id')
            refresh_token = data.get('refresh_token')
            demo = data.get('demo', True)
            
            if not api_key or not api_secret:
                return jsonify({'status': 'error', 'message': 'API key and secret required'}), 400
            
            broker = TradeStationBroker(
                api_key=api_key,
                api_secret=api_secret,
                account_id=account_id,
                refresh_token=refresh_token,
                demo=demo
            )
            
            if broker.authenticate():
                BrokerRegistry._instances['tradestation'] = broker
                config.ACTIVE_BROKER = 'tradestation'
                return jsonify({'status': 'success', 'message': 'TradeStation connected'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Authentication failed'}), 401
        
        else:
            return jsonify({'status': 'error', 'message': f'Unknown broker: {broker_type}'}), 400
            
    except Exception as e:
        logger.error(f"Configure broker error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== MAIN ==========
if __name__ == '__main__':
    logger.info("="*50)
    logger.info("REAPER TRADE COPIER v3.0")
    logger.info("="*50)
    logger.info(f"Brokers: {BrokerRegistry.list_brokers()}")
    logger.info(f"Active: {config.ACTIVE_BROKER}")
    logger.info(f"Account: ${config.ACCOUNT_SIZE}")
    logger.info(f"Sizing: {config.SIZING_MODE}")
    logger.info("="*50)
    
    # Verify active broker is configured
    broker = BrokerRegistry.get_broker(config.ACTIVE_BROKER)
    if not broker:
        logger.warning(f"WARNING: {config.ACTIVE_BROKER} not configured!")
        logger.info("Set environment variables for your broker:")
        logger.info("  Tradovate: TRADOVATE_USERNAME, TRADOVATE_PASSWORD")
        logger.info("  TradeStation: TRADESTATION_API_KEY, TRADESTATION_API_SECRET")
    
    app.run(host='0.0.0.0', port=config.SERVER_PORT, debug=config.DEBUG)