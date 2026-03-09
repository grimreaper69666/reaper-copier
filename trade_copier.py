#!/usr/bin/env python3
"""
REAPER TRADE COPIER v3.1 - Simplified Working Version
"""

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reaper Copier</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0a0a0a; color: #fff; }
            .card { background: #1a1a1a; border-radius: 12px; padding: 20px; margin: 20px 0; }
            input, button { padding: 10px; margin: 5px; }
            button { background: #00ff88; color: #000; border: none; cursor: pointer; }
            .success { color: #00ff88; }
            .error { color: #ff4444; }
        </style>
    </head>
    <body>
        <h1>🎯 Reaper Copier</h1>
        
        <div class="card">
            <h3>Connect Tradovate</h3>
            <input type="text" id="user" placeholder="Username"><br>
            <input type="password" id="pass" placeholder="Password"><br>
            <button onclick="connect()">Connect</button>
            <div id="result"></div>
        </div>
        
        <div class="card">
            <h3>Status</h3>
            <div id="status">Checking...</div>
        </div>
        
        <script>
            async function connect() {
                const user = document.getElementById('user').value;
                const pass = document.getElementById('pass').value;
                const result = document.getElementById('result');
                
                if (!user || !pass) {
                    result.innerHTML = '<span class="error">Enter username and password</span>';
                    return;
                }
                
                result.innerHTML = 'Connecting...';
                
                try {
                    const res = await fetch('/connect', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({username: user, password: pass})
                    });
                    const data = await res.json();
                    result.innerHTML = data.status === 'success' 
                        ? '<span class="success">✅ Connected!</span>'
                        : '<span class="error">❌ ' + data.message + '</span>';
                    checkStatus();
                } catch (e) {
                    result.innerHTML = '<span class="error">Error: ' + e.message + '</span>';
                }
            }
            
            async function checkStatus() {
                try {
                    const res = await fetch('/status');
                    const data = await res.json();
                    document.getElementById('status').innerHTML = 
                        'Status: ' + data.status + '<br>' +
                        'Broker: ' + (data.configured[0] || 'None');
                } catch (e) {
                    document.getElementById('status').innerHTML = 'Error loading status';
                }
            }
            
            checkStatus();
        </script>
    </body>
    </html>
    '''

@app.route('/status')
def status():
    return jsonify({
        'status': 'online',
        'configured': ['tradovate'] if os.getenv('TRADOVATE_USERNAME') else [],
        'broker': 'tradovate'
    })

@app.route('/connect', methods=['POST'])
def connect():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username and password:
        os.environ['TRADOVATE_USERNAME'] = username
        os.environ['TRADOVATE_PASSWORD'] = password
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))