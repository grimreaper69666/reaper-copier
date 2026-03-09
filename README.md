# REAPER TRADE COPIER v3.0
## Modular Trading Bot - Add Any Broker

**No TradersPost subscription. Full management web app.**

---

## WHAT'S NEW IN v3.0

**🎛️ Mission Control Dashboard:**
- Web-based management UI (like TradersPost)
- Real-time P&L tracking
- Position management
- Broker configuration
- Risk settings
- Webhook tester
- System logs

**Plugin Architecture:**
```
BaseBroker (abstract class)
    ├── TradovateBroker (built-in)
    ├── TradeStationBroker (built-in)  
    └── YOUR_CUSTOM_BROKER (you add)
```

---

## QUICK START

### 1. Choose Broker

**Tradovate:**
```bash
export ACTIVE_BROKER=tradovate
export TRADOVATE_USERNAME=your-username
export TRADOVATE_PASSWORD=your-password
export TRADOVATE_ACCOUNT_ID=your-account
export TRADOVATE_DEMO=True  # or False
```

**TradeStation:**
```bash
export ACTIVE_BROKER=tradestation
export TRADESTATION_API_KEY=your-key
export TRADESTATION_API_SECRET=your-secret
export TRADESTATION_ACCOUNT_ID=your-account
export TRADESTATION_REFRESH_TOKEN=your-token
export TRADESTATION_DEMO=True  # or False
```

### 2. Run
```bash
cd ~/.openclaw/reaper-copier
pip install flask requests
python3 trade_copier.py
```

### 3. Open Management UI
```
http://localhost:5000
```

---

## MANAGEMENT UI FEATURES

| Feature | Description |
|---------|-------------|
| **📊 Dashboard** | Real-time P&L, win rate, open positions |
| **📈 Positions** | Manage all positions, close trades |
| **📜 History** | Complete trade history with export |
| **🏦 Brokers** | Configure and switch brokers |
| **🧠 Strategies** | Add/manage trading strategies |
| **🛡️ Risk Settings** | Position sizing, limits, cooldowns |
| **🔔 Webhook Tester** | Test TradingView webhooks |
| **📋 Logs** | View system logs |
| **⚙️ Settings** | General configuration |

---

## UI PREVIEW

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 Reaper Trade Copier          ● System Online            │
├──────────┬──────────────────────────────────────────────────┤
│          │  $1,245.32    $156.20     68.5%      3          │
│  📊      │  Total P&L   Daily P&L   Win Rate   Open        │
│  📈      │                                                  │
│  📜      │  Open Positions                                  │
│          │  ─────────────────────────────────────────      │
│  🏦      │  MNQ   LONG   2   $24,368   $24,200   $24,500   │
│  🧠      │  MES   SHORT  1   $5,234    $5,300    $5,100    │
│  🛡️      │                                                  │
│          │                                                  │
│  🔔      │                                                  │
│  📋      │                                                  │
│  ⚙️      │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

---

## DEFAULT BROKERS

| Broker | Auth | Bracket Orders | Best For |
|--------|------|----------------|----------|
| **Tradovate** | User/Pass | ✅ | Simple setup |
| **TradeStation** | OAuth2 | ⚠️ | Advanced features |

---

## ADDING A NEW BROKER

**Only 4 methods to implement:**

```python
class MyBroker(BaseBroker):
    name = "mybroker"
    
    def authenticate(self) -> bool:
        # Login logic
        return True
    
    def place_order(self, symbol, side, quantity, **kwargs):
        # Order logic
        return {'status': 'success', 'data': {...}}
    
    def get_positions(self) -> List[Dict]:
        return []
    
    def get_orders(self) -> List[Dict]:
        return []
```

**Register it:**
```python
BrokerRegistry.register('mybroker', MyBroker)
BrokerRegistry.create_broker('mybroker', api_key='xxx')
```

**Use it:**
```bash
export ACTIVE_BROKER=mybroker
python3 trade_copier.py
```

---

## API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Management UI (Mission Control) |
| `/status` | GET | System status & stats |
| `/brokers` | GET | List all brokers |
| `/webhook` | POST | TradingView alerts |

---

## TRADINGVIEW WEBHOOK FORMAT

```json
{
  "secret": "your-webhook-secret",
  "symbol": "MNQ",
  "side": "LONG",
  "price": 24368.00,
  "stop_loss": 24200.00,
  "take_profit": 24500.00,
  "strategy": "LuxMACD"
}
```

---

## COST

| Service | Monthly |
|---------|---------|
| TradersPost | $50-200 |
| **Reaper Copier** | **$0** |

**You save $600-2,400/year.**

---

## 📱 MOBILE ACCESS

**Access from your phone just like on PC!**

### Option 1: Quick Mobile Setup (Recommended)
```bash
./mobile-access.sh
```

This will:
- Start the server
- Create a public URL
- **Display a QR code** - scan with your phone!
- Save the URL for later

### Option 2: Check Status
```bash
./status.sh
```

Shows current URL and displays QR code again.

### Mobile Features:
- ✅ Responsive design - works on any screen size
- ✅ Bottom navigation bar (phone-friendly)
- ✅ Touch-optimized buttons
- ✅ Swipe-friendly tables
- ✅ No zoom issues on iOS/Android

---

**Ready to use? Open http://localhost:5000 after starting the server.**

---

## 🌐 SHARE WITH OTHERS

Want a public link to share your dashboard?

### Quick Share (1 minute)
```bash
./start-public.sh
```
Get a public URL like: `https://abc123.ngrok.io`

### Permanent Hosting (10 minutes)
See [DEPLOY.md](DEPLOY.md) for Render/Railway deployment.

**Shareable link:** `https://your-app.render.com`