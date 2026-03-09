#!/bin/bash
# Deploy to Railway.app (No GitHub required!)

echo "🚂 Deploying to Railway.app (Free Forever)"
echo "============================================"
echo ""

# Check if railway is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Verify installation
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI installation failed"
    exit 1
fi

echo "✓ Railway CLI installed"
echo ""

# Login (opens browser)
echo "🔐 Logging in to Railway..."
echo "   A browser window will open. Just click 'Authorize'."
railway login
echo ""

# Create new project
echo "📁 Creating new project..."
cd ~/.openclaw/reaper-copier
railway init --name reaper-copier

echo ""
echo "⚙️ Configuring environment variables..."

# Set environment variables
railway variables set WEBHOOK_SECRET="your-webhook-secret-$(date +%s)"
railway variables set ACTIVE_BROKER="tradovate"
railway variables set TRADOVATE_DEMO="True"
railway variables set ACCOUNT_SIZE="10000"
railway variables set RISK_PER_TRADE="0.02"
railway variables set SIZING_MODE="risk"

echo "✓ Environment configured"
echo ""

# Deploy
echo "🚀 Deploying..."
railway up --detach

echo ""
echo "🌐 Getting public URL..."
sleep 5

URL=$(railway domain 2>&1 | grep -o "https://[^[:space:]]*" || echo "")

if [ -n "$URL" ]; then
    echo ""
    echo "================================================"
    echo "✅ DEPLOYMENT COMPLETE!"
    echo ""
    echo "🔗 YOUR PERMANENT URL:"
    echo "   $URL"
    echo ""
    echo "📱 Open this on your phone - it works forever!"
    echo "   (Even when your Mac is off)"
    echo ""
    
    # Generate QR code
    if command -v qrencode &> /dev/null; then
        echo "📱 QR Code:"
        qrencode -t ANSI "$URL"
    fi
    
    echo ""
    echo "⚠️  To add your broker credentials:"
    echo "   railway variables set TRADOVATE_USERNAME=your-username"
    echo "   railway variables set TRADOVATE_PASSWORD=your-password"
    echo ""
    echo "================================================"
    
    # Save URL
    echo "$URL" > .permanent_url
else
    echo "⏳ Deployment in progress..."
    echo "   Check status: railway status"
    echo "   Your URL will appear soon: railway domain"
fi