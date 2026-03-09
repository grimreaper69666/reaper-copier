#!/bin/bash
# Deploy Reaper Trade Copier to Render.com (Free Forever)

echo "🚀 Deploying Reaper Trade Copier to Render.com"
echo "================================================"
echo ""

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "📦 Installing Render CLI..."
    curl -fsSL https://render.com/install/render-cli.sh | bash
    export PATH="$HOME/.render/bin:$PATH"
fi

# Verify render is available
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI not found. Please install manually:"
    echo "   curl -fsSL https://render.com/install/render-cli.sh | bash"
    exit 1
fi

echo "✓ Render CLI installed"
echo ""

# Login to Render
echo "🔐 Logging in to Render..."
echo "   (A browser window will open for authentication)"
render login
echo ""

# Create blueprint
echo "📋 Creating deployment blueprint..."
cd ~/.openclaw/reaper-copier

# Create render.yaml if it doesn't exist
if [ ! -f render.yaml ]; then
cat > render.yaml <> 'EOF'
services:
  - type: web
    name: reaper-copier
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python trade_copier.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        value: 10000
      - key: WEBHOOK_SECRET
        generateValue: true
      - key: ACTIVE_BROKER
        value: tradovate
      - key: TRADOVATE_DEMO
        value: "True"
      - key: ACCOUNT_SIZE
        value: "10000"
      - key: RISK_PER_TRADE
        value: "0.02"
      - key: SIZING_MODE
        value: risk
EOF
fi

echo "✓ Blueprint created"
echo ""

# Deploy
echo "🚀 Starting deployment..."
echo "   This may take a few minutes..."
echo ""

render blueprint apply

echo ""
echo "================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Your app will be available at:"
echo "   https://reaper-copier.onrender.com"
echo ""
echo "⚠️  IMPORTANT: Set your broker credentials in the Render dashboard:"
echo "   1. Go to https://dashboard.render.com"
echo "   2. Select 'reaper-copier' service"
echo "   3. Click 'Environment' tab"
echo "   4. Add your credentials:"
echo "      - TRADOVATE_USERNAME"
echo "      - TRADOVATE_PASSWORD"
echo "      - TRADOVATE_ACCOUNT_ID"
echo ""
echo "🔗 Dashboard: https://dashboard.render.com"
echo "================================================"