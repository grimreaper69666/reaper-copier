#!/bin/bash
# Deploy Reaper Trade Copier without GitHub
# Using Render's Deploy from ZIP feature

echo "🚀 Deploying to Render.com (No GitHub Required)"
echo "================================================="
echo ""

# Create a deploy package
echo "📦 Creating deployment package..."
cd ~/.openclaw/reaper-copier

# Clean up unnecessary files
rm -f server.log ngrok.log tunnel.log trades.log qr-code.png .last_url ngrok.pid

# Create ZIP of the project
zip -r reaper-copier-deploy.zip . -x "*.git*" -x "*.pyc" -x "__pycache__/*"

echo "✓ Package created: reaper-copier-deploy.zip"
echo ""

# Instructions for manual deploy
cat <> 'EOF'

🎯 NEXT STEPS (2 minutes):

1. Go to https://dashboard.render.com
2. Sign up with your email (free)
3. Click "New +" → "Web Service"
4. Select "Deploy from ZIP"
5. Upload: reaper-copier-deploy.zip
6. Settings:
   - Name: reaper-copier
   - Runtime: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: python trade_copier.py
7. Click "Create Web Service"

Your app will be live at:
   https://reaper-copier.onrender.com

📱 Save this URL to your phone's home screen!

EOF

echo ""
echo "📋 Instructions saved to DEPLOY_INSTRUCTIONS.txt"
echo ""
echo "🌐 Opening Render dashboard..."
sleep 2
open "https://dashboard.render.com"

echo ""
echo "✅ Deployment package ready!"
echo "   File: ~/.openclaw/reaper-copier/reaper-copier-deploy.zip"
echo ""
echo "Follow the instructions above to complete deployment."