#!/bin/bash
# REAPER COPIER - Mobile Access Setup
# Creates a public URL you can access from your phone

echo "📱 Reaper Trade Copier - Mobile Access"
echo "======================================="

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    brew install ngrok
fi

# Check if qrencode is installed for QR codes
if ! command -v qrencode &> /dev/null; then
    echo "📦 Installing qrencode for QR codes..."
    brew install qrencode
fi

# Kill any existing processes
pkill -f "python3 trade_copier.py" 2>/dev/null
pkill -f "ngrok" 2>/dev/null
sleep 2

echo ""
echo "🚀 Starting Reaper Trade Copier..."

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Set defaults
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-"your-webhook-secret"}
export ACTIVE_BROKER=${ACTIVE_BROKER:-"tradovate"}
export TRADOVATE_DEMO=${TRADOVATE_DEMO:-"True"}
export ACCOUNT_SIZE=${ACCOUNT_SIZE:-"10000"}
export RISK_PER_TRADE=${RISK_PER_TRADE:-"0.02"}
export SIZING_MODE=${SIZING_MODE:-"risk"}
export PORT=${PORT:-"5000"}

# Start the trade copier
python3 trade_copier.py > server.log 2>&1 &
COPIER_PID=$!
echo "✓ Trade Copier started (PID: $COPIER_PID)"

sleep 3

# Start ngrok with a reserved subdomain if available
echo ""
echo "🌐 Starting public tunnel..."
echo "   (This may take a few seconds...)"

ngrok http http://localhost:$PORT --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 8

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)

if [ -z "$PUBLIC_URL" ]; then
    echo "⚠️  Could not get public URL. Retrying in 5 seconds..."
    sleep 5
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)
fi

if [ -n "$PUBLIC_URL" ]; then
    echo ""
    echo "======================================="
    echo "🔗 YOUR PUBLIC URL:"
    echo "   $PUBLIC_URL"
    echo ""
    echo "📊 Dashboard: $PUBLIC_URL"
    echo "🔔 Webhook:   $PUBLIC_URL/webhook"
    echo "📈 Status:    $PUBLIC_URL/status"
    echo "======================================="
    echo ""
    
    # Generate QR code
    if command -v qrencode &> /dev/null; then
        echo "📱 Scan this QR code with your phone:"
        echo ""
        qrencode -t ANSI "$PUBLIC_URL"
        echo ""
    fi
    
    echo "✅ Ready! You can now:"
    echo "   1. Open the URL on your PC browser"
    echo "   2. Scan the QR code with your phone"
    echo "   3. Share the link with others"
    echo ""
    echo "⚠️  NOTE: This URL is temporary."
    echo "   For a permanent URL, deploy to Render/Railway."
    echo "   See DEPLOY.md for instructions."
    echo ""
    echo "🛑 To stop, run: kill $COPIER_PID $NGROK_PID"
    echo ""
    
    # Save the URL to a file for reference
    echo "$PUBLIC_URL" > .last_url
    
else
    echo "❌ Failed to create public URL"
    echo "Check ngrok.log for errors"
    kill $COPIER_PID $NGROK_PID 2>/dev/null
    exit 1
fi

# Keep script running to show logs
echo "📋 Server logs (Ctrl+C to stop viewing, server keeps running):"
tail -f server.log