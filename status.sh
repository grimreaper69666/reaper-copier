#!/bin/bash
# Quick status check for Reaper Trade Copier
# Shows current URL and server status

echo "📱 Reaper Trade Copier - Quick Status"
echo "======================================"

# Check if server is running
if pgrep -f "python3 trade_copier.py" > /dev/null; then
    echo "✅ Server: RUNNING"
    
    # Check for saved URL
    if [ -f .last_url ]; then
        URL=$(cat .last_url)
        echo "🌐 Public URL: $URL"
        
        # Test if URL is still active
        if curl -s "$URL/status" > /dev/null 2>&1; then
            echo "✅ Public URL: ACTIVE"
            
            # Show QR code
            if command -v qrencode &> /dev/null; then
                echo ""
                echo "📱 Scan to open on your phone:"
                qrencode -t ANSI "$URL"
            fi
        else
            echo "⚠️  Public URL: NOT RESPONDING (restart with ./mobile-access.sh)"
        fi
    else
        echo "⚠️  No public URL found. Run ./mobile-access.sh to create one."
    fi
    
    # Show local access
    echo ""
    echo "💻 Local access: http://localhost:5000"
    
else
    echo "❌ Server: NOT RUNNING"
    echo ""
    echo "To start:"
    echo "  ./mobile-access.sh  # With public URL"
    echo "  python3 trade_copier.py  # Local only"
fi

echo ""
echo "======================================"
echo "Last updated: $(date)
