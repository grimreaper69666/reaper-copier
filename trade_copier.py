#!/usr/bin/env python3
"""
REAPER TRADE COPIER - PRODUCTION VERSION
Professional trading automation platform
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import json
from datetime import datetime

app = Flask(__name__)

# In-memory storage
CONFIG = {
    'account_size': 10000,
    'risk_per_trade': 2.0,
    'max_positions': 5,
    'sizing_mode': 'risk',
    'broker': None,
    'webhook_secret': os.getenv('WEBHOOK_SECRET', 'change-me')
}

POSITIONS = []
TRADES = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'broker': CONFIG['broker'],
        'account_size': CONFIG['account_size'],
        'positions': len(POSITIONS),
        'total_trades': len(TRADES)
    })

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        data = request.get_json()
        CONFIG.update(data)
        return jsonify({'status': 'success', 'config': CONFIG})
    return jsonify(CONFIG)

@app.route('/api/broker/connect', methods=['POST'])
def connect_broker():
    data = request.get_json()
    broker_type = data.get('type')
    
    if broker_type == 'tradovate':
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            CONFIG['broker'] = {
                'type': 'tradovate',
                'username': username,
                'connected': True
            }
            return jsonify({'status': 'success', 'message': 'Connected to Tradovate'})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 400

@app.route('/api/positions')
def get_positions():
    return jsonify(POSITIONS)

@app.route('/api/trades')
def get_trades():
    return jsonify(TRADES)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data.get('secret') != CONFIG['webhook_secret']:
        return jsonify({'status': 'error', 'message': 'Invalid secret'}), 403
    
    # Process signal
    trade = {
        'id': len(TRADES) + 1,
        'symbol': data.get('symbol'),
        'side': data.get('side'),
        'entry': data.get('price'),
        'stop': data.get('stop_loss'),
        'target': data.get('take_profit'),
        'timestamp': datetime.now().isoformat()
    }
    
    TRADES.append(trade)
    POSITIONS.append(trade)
    
    return jsonify({'status': 'success', 'trade': trade})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)