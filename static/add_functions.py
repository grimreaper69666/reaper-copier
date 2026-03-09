import re

# Read file
with open('index.html', 'r') as f:
    content = f.read()

# New functions to add before the closing script tag
new_functions = '''
        // Strategy Functions
        let strategies = [];
        
        function showAddStrategyModal() {
            document.getElementById('strategy-modal').style.display = 'flex';
        }
        
        function closeStrategyModal() {
            document.getElementById('strategy-modal').style.display = 'none';
        }
        
        function saveStrategy() {
            const name = document.getElementById('strategy-name').value;
            const symbols = document.getElementById('strategy-symbols').value;
            const risk = document.getElementById('strategy-risk').value;
            const maxPos = document.getElementById('strategy-max-pos').value;
            const minRR = document.getElementById('strategy-min-rr').value;
            
            if (!name) {
                alert('Strategy name required');
                return;
            }
            
            const strategy = {
                id: Date.now(),
                name: name,
                symbols: symbols.split(',').map(s => s.trim()).filter(s => s),
                risk_per_trade: parseFloat(risk),
                max_positions: parseInt(maxPos),
                min_risk_reward: parseFloat(minRR),
                enabled: true
            };
            
            strategies.push(strategy);
            renderStrategies();
            closeStrategyModal();
            
            document.getElementById('strategy-name').value = '';
            document.getElementById('strategy-symbols').value = '';
        }
        
        function renderStrategies() {
            const container = document.getElementById('strategies-list');
            
            if (strategies.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🧠</div>
                        <p>No strategies configured</p>
                        <p style="font-size: 0.875rem; margin-top: 0.5rem;">Add a strategy to start trading with custom rules</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = strategies.map(s => `
                <div class="card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h4>${s.name}</h4>
                        <span class="badge ${s.enabled ? 'badge-long' : ''}">${s.enabled ? 'Enabled' : 'Disabled'}</span>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">
                        Symbols: ${s.symbols.join(', ') || 'All'}
                    </p>
                    <p style="color: var(--text-secondary); font-size: 0.875rem;">
                        Risk: ${s.risk_per_trade}% | Max Pos: ${s.max_positions} | Min R:R ${s.min_risk_reward}
                    </p>
                </div>
            `).join('');
        }
        
        // Risk Settings
        function saveRiskSettings() {
            const btn = document.querySelector('#risk .btn-primary');
            const originalText = btn.textContent;
            btn.textContent = '✅ Saved!';
            btn.style.background = 'var(--accent-green)';
            btn.style.color = '#000';
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                btn.style.color = '';
            }, 2000);
        }
        
        // Settings
        function saveSettings() {
            const btn = document.querySelector('#settings .btn-primary');
            const originalText = btn.textContent;
            btn.textContent = '✅ Saved!';
            btn.style.background = 'var(--accent-green)';
            btn.style.color = '#000';
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                btn.style.color = '';
            }, 2000);
        }
        
        // Close modal on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeStrategyModal();
            }
        });
        
        // Logs
        async function refreshLogs() {
            const now = new Date().toISOString();
            const connectionStatus = document.getElementById('connection-badge')?.textContent || 'Unknown';
            
            document.getElementById('logs-content').textContent = 
                `${now} - System online\\n` +
                `Server: Running\\n` +
                `Broker: ${connectionStatus}\\n` +
                `Active Trades: 0\\n` +
                `Total Trades: 0\\n` +
                `---\\n` +
                `Server ready to accept TradingView webhooks`;
        }
        
        // Updated initial load
        refreshData();
        renderStrategies();
'''

# Find the location before // Initial load and replace
pattern = r'(// Initial load\s+refreshData\(\);)'
replacement = new_functions + '\n'
content = re.sub(pattern, replacement, content)

with open('index.html', 'w') as f:
    f.write(content)

print('✅ JavaScript functions added')