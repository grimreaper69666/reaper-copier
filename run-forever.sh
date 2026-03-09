#!/bin/bash
# REAPER COPIER - AUTO-RECONNECT FOREVER
# Keeps your trading bot online even if connection drops

cd ~/.openclaw/reaper-copier

echo "🎯 Reaper Copier - Auto-Reconnect Mode"
echo "========================================"
echo ""
echo "This will:"
echo "  ✓ Keep your server running"
echo "  ✓ Auto-create new public URLs if connection drops"
echo "  ✓ Save the current URL to a file"
echo "  ✓ Run forever (even if you close terminal with 'disown')"
echo ""
read -p "Press Enter to start..."

# Kill any existing
pkill -f "python3 trade_copier.py" 2>/dev/null
pkill -f "lt -p 5000" 2>/dev/null
sleep 2

# Environment
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-"reaper-secret-$(date +%s)"}
export ACTIVE_BROKER=${ACTIVE_BROKER:-"tradovate"}
export TRADOVATE_DEMO="True"
export ACCOUNT_SIZE="10000"
export RISK_PER_TRADE="0.02"
export SIZING_MODE="risk"
export PORT="5000"

# Start server
echo "🚀 Starting server..."
python3 trade_copier.py > server.log 2>&1 &
disown %1 2>/dev/null || true
sleep 3

# Function to start tunnel
start_tunnel() {
    while true; do
        echo "🌐 Creating public tunnel..."
        
        # Kill old tunnel
        pkill -f "lt -p 5000" 2>/dev/null
        sleep 1
        
        # Start new tunnel
        npx localtunnel --port 5000 > tunnel.log 2>&1 &
disown %1 2>/dev/null || true
        
        sleep 6
        
        # Get URL
        URL=$(grep -o "https://[a-zA-Z0-9-]*\.loca\.lt" tunnel.log | head -1)
        
        if [ -n "$URL" ]; then
            echo ""
            echo "╔════════════════════════════════════════════════╗"
            echo "║  🔗 YOUR URL (Updated: $(date '+%I:%M %p'))"
            echo "║                                                ║"
            echo "║  $URL"
            echo "║                                                ║"
            echo "╚════════════════════════════════════════════════╝"
            echo ""
            echo "$URL" > .current_url
            
            # Show QR
            if command -v qrencode &> /dev/null; then
                qrencode -t ANSI "$URL"
            fi
            
            echo ""
            echo "📱 This URL is active. If it disconnects, a new one will appear."
            echo "💾 URL saved to: ~/.openclaw/reaper-copier/.current_url"
            echo ""
            
            # Send notification if possible
            if command -v osascript &> /dev/null; then
                osascript -e "display notification \"$URL\" with title \"Reaper Copier URL\""
            fi
        fi
        
        # Wait for tunnel to die
        sleep 10
        while pgrep -f "lt -p 5000" > /dev/null; do
            sleep 30
        done
        
        echo "⚠️  Connection lost. Creating new URL in 5 seconds..."
        sleep 5
    done
}

# Start tunnel manager
start_tunnel &

# Save PID
echo $! > .autoreconnect.pid

echo "✅ Auto-reconnect started!"
echo ""
echo "📝 To check current URL anytime:"
echo "   cat ~/.openclaw/reaper-copier/.current_url"
echo ""
echo "🛑 To stop everything:"
echo "   pkill -f 'python3 trade_copier.py'"
echo "   pkill -f 'lt -p 5000'"
echo ""
echo "💡 Tip: Keep your Mac plugged in and don't sleep for 24/7 operation"
echo "   System Preferences → Energy → Prevent automatic sleep"
echo ""
echo "🔔 New URLs will appear here automatically when connection drops."
echo ""

# Keep showing updates
tail -f server.log