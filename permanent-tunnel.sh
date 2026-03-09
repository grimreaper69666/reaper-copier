#!/bin/bash
# PERMANENT TUNNEL - Auto-reconnecting
# This keeps your Reaper Copier accessible even after disconnects

cd ~/.openclaw/reaper-copier

# Kill any existing processes
pkill -f "python3 trade_copier.py" 2>/dev/null
pkill -f "lt -p 5000" 2>/dev/null
sleep 2

# Start server
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-"demo-secret-$(date +%s)"}
export ACTIVE_BROKER=${ACTIVE_BROKER:-"tradovate"}
export TRADOVATE_DEMO="True"
export ACCOUNT_SIZE="10000"
export RISK_PER_TRADE="0.02"
export SIZING_MODE="risk"
export PORT="5000"

python3 trade_copier.py > server.log 2>&1 &
echo $! > .server.pid
sleep 3

echo "✅ Server running on http://localhost:5000"
echo ""

# Start tunnel with auto-reconnect
while true; do
    echo "🌐 Starting public tunnel..."
    
    # Use localtunnel with subdomain attempt
    npx localtunnel --port 5000 --subdomain reaper-$(date +%s | tail -c 5) > tunnel.log 2>&1 &
    TUNNEL_PID=$!
    echo $TUNNEL_PID > .tunnel.pid
    
    sleep 6
    
    # Get and display URL
    URL=$(grep -o "https://[a-zA-Z0-9-]*\.loca\.lt" tunnel.log | head -1)
    
    if [ -n "$URL" ]; then
        echo ""
        echo "╔════════════════════════════════════════════════╗"
        echo "║  🔗 YOUR PUBLIC URL                            ║"
        echo "║                                                ║"
        echo "║  $URL"
        echo "║                                                ║"
        echo "╚════════════════════════════════════════════════╝"
        echo ""
        echo "📱 Scan QR code or visit URL on your phone"
        echo ""
        qrencode -t ANSI "$URL" 2>/dev/null || echo "(Install qrencode for QR: brew install qrencode)"
        echo ""
        echo "⚠️  This URL is active. If it disconnects, a new one will be created."
        echo "📝 URL saved to: ~/.openclaw/reaper-copier/.current_url"
        echo "$URL" > .current_url
        echo ""
        echo "Press Ctrl+C to stop. Server will keep running."
    fi
    
    # Wait for tunnel to die, then restart
    wait $TUNNEL_PID
    echo "⚠️  Tunnel disconnected. Reconnecting in 5 seconds..."
    sleep 5
done