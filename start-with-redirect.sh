#!/bin/bash
# Keep Reaper Copier running with a persistent redirect

cd ~/.openclaw/reaper-copier

# Create redirect page
mkdir -p redirect
cat > redirect/index.html <> 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reaper Copier - Connecting...</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {
            font-family: -apple-system, sans-serif;
            background: #0a0a0f;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            text-align: center;
        }
        .loading {
            width: 50px;
            height: 50px;
            border: 3px solid #333;
            border-top-color: #00ff88;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        h1 { margin: 10px 0; }
        p { color: #888; }
        .url { color: #00ff88; font-size: 1.2rem; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="loading"></div>
    <h1>🎯 Reaper Copier</h1>
    <p>Connecting to your server...</p>
    <div class="url" id="url">Loading...</div>
    <script>
        // Try to fetch current URL from status endpoint
        fetch('/current-url')
            .then(r => r.text())
            .then(url => {
                if(url && url.startsWith('http')) {
                    window.location.href = url;
                } else {
                    document.getElementById('url').textContent = 'Server starting up...';
                }
            })
            .catch(() => {
                document.getElementById('url').textContent = 'Retrying in 5 seconds...';
            });
    </script>
</body>
</html>
HTMLEOF

# Start the redirect server
python3 -m http.server 8080 --directory redirect > redirect-server.log 2>&1 &
echo $! > .redirect.pid

echo "✅ Redirect page ready"

# Now start the main tunnel
./mobile-access.sh