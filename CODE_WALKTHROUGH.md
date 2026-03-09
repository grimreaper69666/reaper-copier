# REAPER TRADE COPIER - CODE WALKTHROUGH

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│  TRADINGVIEW                                            │
│  (Sends webhook alerts)                                 │
└─────────────┬───────────────────────────────────────────┘
              │ POST /webhook
              ▼
┌─────────────────────────────────────────────────────────┐
│  FLASK SERVER (trade_copier.py)                         │
│  ├─ Webhook Handler (receives alerts)                   │
│  ├─ Trade Manager (tracks positions)                    │
│  ├─ Broker Registry (manages brokers)                   │
│  └─ Web UI (static/index.html)                          │
└─────────────┬───────────────────────────────────────────┘
              │ API calls
              ▼
┌─────────────────────────────────────────────────────────┐
│  BROKER API (Tradovate/TradeStation)                    │
│  └─ Executes actual trades                              │
└─────────────────────────────────────────────────────────┘
```

---

## FILE STRUCTURE

```
reaper-copier/
├── trade_copier.py          # Main server (700 lines)
│   ├── Config               # Environment variables
│   ├── BaseBroker           # Abstract broker class
│   ├── TradovateBroker      # Tradovate implementation
│   ├── TradeStationBroker   # TradeStation implementation
│   ├── BrokerRegistry       # Plugin system
│   ├── Trade                # Data model
│   ├── TradeManager         # Position tracking
│   ├── NotificationManager  # Discord/Telegram
│   └── Flask routes         # Web server
│
├── static/
│   ├── index.html           # Management UI (1000+ lines)
│   └── mobile.css           # Mobile styles
│
├── requirements.txt         # Python dependencies
├── render.yaml              # Render.com config
└── README.md                # Documentation
```

---

## KEY COMPONENTS

### 1. CONFIGURATION (Lines 45-96)

```python
class Config:
    # Reads from environment variables
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'change-this-key')
    ACTIVE_BROKER = os.getenv('ACTIVE_BROKER', 'tradovate')
    ACCOUNT_SIZE = float(os.getenv('ACCOUNT_SIZE', 10000))
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 0.02))
```

**What it does:**
- Reads settings from environment variables
- Sets defaults if not provided
- Makes app configurable without changing code

**How to use:**
```bash
export ACTIVE_BROKER=tradovate
export TRADOVATE_USERNAME=yourname
export TRADOVATE_PASSWORD=yourpass
python trade_copier.py
```

---

### 2. BASE BROKER CLASS (Lines 99-128)

```python
class BaseBroker(ABC):
    """Abstract class - all brokers must implement this"""
    
    @abstractmethod
    def authenticate(self) -> bool:
        pass
    
    @abstractmethod  
    def place_order(self, symbol, side, quantity, **kwargs) -> Dict:
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        pass
```

**What it does:**
- Defines the "contract" all brokers must follow
- Ensures every broker has: authenticate, place_order, get_positions
- Lets you add new brokers easily

**How to add a broker:**
```python
class MyBroker(BaseBroker):
    def authenticate(self) -> bool:
        # Your auth logic
        return True
    
    def place_order(self, symbol, side, quantity, **kwargs):
        # Your order logic
        return {'status': 'success'}
    
    def get_positions(self):
        return []
```

---

### 3. TRADOVATE BROKER (Lines 131-247)

```python
class TradovateBroker(BaseBroker):
    """Full Tradovate API implementation"""
    
    BASE_URL = 'https://live.tradovateapi.com/v1'
    DEMO_URL = 'https://demo.tradovateapi.com/v1'
```

**Key methods:**

**`authenticate()`** - Logs in to Tradovate
```python
def authenticate(self) -> bool:
    response = requests.post(
        f"{self.base_url}/auth/accesstokenrequest",
        json={'name': self.username, 'password': self.password, ...}
    )
    self.access_token = response.json()['accessToken']
    return True
```

**`place_order()`** - Sends order to Tradovate
```python
def place_order(self, symbol, side, quantity, stop_loss, take_profit):
    order_spec = {
        'symbol': symbol,
        'action': 'Buy' if side == 'LONG' else 'Sell',
        'orderQty': quantity,
        'bracket': {'stopLoss': stop_loss, 'profitTarget': take_profit}
    }
    response = requests.post(f"{self.base_url}/order/placeorder", ...)
    return {'status': 'success', 'data': response.json()}
```

---

### 4. BROKER REGISTRY (Lines 343-400)

```python
class BrokerRegistry:
    """Plugin system - register any broker"""
    
    _brokers: Dict[str, Type[BaseBroker]] = {}
    
    @classmethod
    def register(cls, name: str, broker_class: Type[BaseBroker]):
        cls._brokers[name] = broker_class
```

**What it does:**
- Maintains list of available brokers
- Creates broker instances
- Lets you switch brokers at runtime

**Usage:**
```python
# Register built-in brokers
BrokerRegistry.register('tradovate', TradovateBroker)
BrokerRegistry.register('tradestation', TradeStationBroker)

# Create instance
BrokerRegistry.create_broker('tradovate', username='xxx', password='yyy')

# Get active broker
broker = BrokerRegistry.get_broker('tradovate')
```

---

### 5. TRADE MANAGER (Lines 417-540)

```python
class TradeManager:
    """Manages all trading operations"""
    
    def __init__(self):
        self.positions: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []
        self.daily_pnl = 0.0
```

**Key methods:**

**`can_trade()`** - Checks if trading is allowed
```python
def can_trade(self) -> tuple[bool, str]:
    # Check cooldown
    if time_since_last < config.COOLDOWN_MINUTES:
        return False, "Cooldown active"
    
    # Check max positions
    if len(self.positions) >= config.MAX_POSITIONS:
        return False, "Max positions reached"
    
    # Check daily loss limit
    if self.daily_pnl < -max_daily_loss:
        return False, "Daily loss limit"
    
    return True, "OK"
```

**`calculate_size()`** - Position sizing
```python
def calculate_size(self, entry: float, stop: float, symbol: str) -> int:
    if config.SIZING_MODE == 'fixed':
        return config.FIXED_QUANTITY
    
    elif config.SIZING_MODE == 'risk':
        risk_amount = config.ACCOUNT_SIZE * config.RISK_PER_TRADE
        risk_per_contract = abs(entry - stop) * point_value
        return max(1, int(risk_amount / risk_per_contract))
    
    elif config.SIZING_MODE == 'kelly':
        # Kelly Criterion formula
        ...
```

---

### 6. WEBHOOK HANDLER (Lines 630-700)

```python
@app.route('/webhook', methods=['POST'])
def webhook():
    """TradingView sends alerts here"""
    
    # 1. Parse incoming data
    data = request.get_json()
    
    # 2. Verify secret (security)
    if data.get('secret') != config.WEBHOOK_SECRET:
        return {'status': 'error', 'message': 'Invalid secret'}, 403
    
    # 3. Extract signal details
    symbol = data.get('symbol', 'MNQ')
    side = data.get('side', 'LONG')
    entry = float(data.get('price', 0))
    stop = data.get('stop_loss')
    target = data.get('take_profit')
    
    # 4. Check if can trade
    can_trade, reason = trade_manager.can_trade()
    if not can_trade:
        return {'status': 'rejected', 'reason': reason}
    
    # 5. Calculate position size
    quantity = trade_manager.calculate_size(entry, stop, symbol)
    
    # 6. Place order with broker
    broker = BrokerRegistry.get_broker(config.ACTIVE_BROKER)
    result = broker.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        stop_loss=stop,
        take_profit=target
    )
    
    # 7. Track the trade
    if result['status'] == 'success':
        trade = Trade(...)
        trade_manager.add_trade(trade)
        notification_manager.notify(f"New {side} Position", ...)
    
    return {'status': 'success', 'trade': trade.to_dict()}
```

**Flow:**
```
TradingView Alert → POST /webhook → Verify Secret → 
Check Limits → Calculate Size → Place Order → 
Track Position → Send Notification
```

---

### 7. WEB UI (static/index.html)

**Structure:**
```html
┌────────────────────────────────────┐
│ Header (Logo + Status)             │
├────────────────────────────────────┤
│ Sidebar    │  Main Content         │
│            │                       │
│ 📊 Dashboard│  [Stats Cards]       │
│ 📈 Positions│  [Positions Table]   │
│ 📜 History │                       │
│ 🏦 Brokers │  [Active Section]     │
│ ...        │                       │
└────────────────────────────────────┘
```

**Key features:**
- **Responsive design** - Works on mobile/desktop
- **Bottom navigation** - Mobile-friendly
- **Auto-refresh** - Dashboard updates every 5 seconds
- **QR code ready** - Easy phone access

---

## DATA FLOW

### When TradingView Sends an Alert:

```
1. TradingView detects signal (e.g., LuxMACD buy)
2. Sends POST to /webhook with JSON:
   {
     "secret": "xxx",
     "symbol": "MNQ",
     "side": "LONG",
     "price": 24368,
     "stop_loss": 24200,
     "take_profit": 24500
   }

3. Flask receives webhook
4. Verifies secret key (prevents fake signals)
5. Checks trading limits (max positions, cooldown, etc.)
6. Calculates position size (based on risk %)
7. Sends order to Tradovate API
8. Tradovate executes trade
9. We track the position in memory
10. Send Discord/Telegram notification
11. Update web dashboard
```

---

## HOW TO MODIFY

### Add a New Broker:
```python
class InteractiveBrokers(BaseBroker):
    name = "interactivebrokers"
    
    def authenticate(self):
        # Connect to IB
        return True
    
    def place_order(self, symbol, side, quantity, **kwargs):
        # IB order logic
        return {'status': 'success'}

# Register it
BrokerRegistry.register('interactivebrokers', InteractiveBrokers)
```

### Change Position Sizing:
```python
# Edit config or set env var
export SIZING_MODE=kelly  # Options: fixed, percent, risk, kelly
export RISK_PER_TRADE=0.01  # 1% instead of 2%
```

### Add Notification Channel:
```python
# In NotificationManager.__init__
if config.SLACK_WEBHOOK:
    self.channels.append('slack')

# Add method
def _send_slack(self, title, message):
    requests.post(config.SLACK_WEBHOOK, json={'text': message})
```

---

## KEY DESIGN DECISIONS

1. **Environment Variables** - No hardcoded secrets
2. **Abstract Base Class** - Easy to add brokers
3. **In-Memory Storage** - Fast, no database needed
4. **Risk Management** - Built-in limits and checks
5. **Async Notifications** - Don't block trading
6. **Mobile-First UI** - Trade from anywhere

---

## QUESTIONS?

Want me to explain any specific part deeper?