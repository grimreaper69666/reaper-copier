#!/bin/bash
# REAPER COPIER - Public Access Setup
# This script sets up ngrok for temporary public URL

echo "🎯 Reaper Trade Copier - Public Access Setup"
echo "============================================"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    brew install ngrok
fi

# Check if authtoken is set
if ! ngrok config check &> /dev/null; then
    echo ""
    echo "⚠️  Ngrok requires an authtoken"
    echo "1. Sign up at https://dashboard.ngrok.com/signup"
    echo "2. Get your token from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo ""
    read -p "Paste your ngrok authtoken: " TOKEN
    ngrok config add-authtoken $TOKEN
fi

# Kill any existing processes
pkill -f "python3 trade_copier.py" 2>/dev/null
pkill -f "ngrok" 2>/dev/null
sleep 2

echo ""
echo "🚀 Starting Reaper Trade Copier..."

# Start the trade copier in background
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-"your-webhook-secret"}
export ACTIVE_BROKER=${ACTIVE_BROKER:-"tradovate"}
export TRADOVATE_DEMO=${TRADOVATE_DEMO:-"True"}
export ACCOUNT_SIZE=${ACCOUNT_SIZE:-"10000"}
export RISK_PER_TRADE=${RISK_PER_TRADE:-"0.02"}
export SIZING_MODE=${SIZING_MODE:-"risk"}
export PORT=${PORT:-"5000"}

python3 trade_copier.py > server.log 2>&1 &
COPIER_PID=$!
echo "✓ Trade Copier started (PID: $COPIER_PID)"

sleep 3

# Start ngrok
echo ""
echo "🌐 Starting ngrok tunnel..."
ngrok http http://localhost:$PORT --log=stdout &
NGROK_PID=$!

sleep 5

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)

echo ""
echo "============================================"
echo "🔗 YOUR PUBLIC URL:"
echo "   $PUBLIC_URL"
echo ""
echo "📊 Management UI: $PUBLIC_URL"
echo "🔔 Webhook URL:  $PUBLIC_URL/webhook"
echo "📈 Status API:   $PUBLIC_URL/status"
echo "============================================"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - This URL is temporary (changes when restarted)"
echo "   - For permanent URL, deploy to Render/Railway"
echo "   - Share the link with others to let them see your dashboard"
echo ""
echo "🛑 To stop:"
echo "   kill $COPIER_PID $NGROK_PID"
echo ""
echo "Press Ctrl+C to stop viewing logs (server keeps running)"
tail -f server.log