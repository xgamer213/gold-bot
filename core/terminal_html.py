"""
HTML & Client-Side UI for Ahmed's Institutional Gold Trading Terminal.
Provides an interactive live TradingView candlestick chart for XAU/USD,
autonomous Smart Money Concepts (SMC) confluence scanner, real-time news radar,
and an embedded AI trade conversation assistant.
"""

def get_terminal_html(user_name: str = "Ahmed", account_balance: float = 10000.0, risk_percent: float = 1.0, min_confluence: int = 85) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Gold Sniper AI • Institutional Trading Terminal | {user_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --bg-dark: #090d16;
      --bg-panel: #0f172a;
      --bg-card: #1e293b;
      --border-color: #334155;
      --gold-primary: #f59e0b;
      --gold-hover: #d97706;
      --green-bull: #10b981;
      --red-bear: #ef4444;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg-dark); }}
    ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--gold-primary); }}

    /* Top Navigation Bar */
    header {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border-color);
      padding: 10px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      z-index: 10;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .brand-logo {{
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #f59e0b, #b45309);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      color: #0f172a;
      font-size: 18px;
    }}
    .brand-text h1 {{
      font-size: 16px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: 0.5px;
    }}
    .brand-text span {{
      font-size: 11px;
      color: var(--gold-primary);
      text-transform: uppercase;
      letter-spacing: 1px;
    }}

    /* Radar Badges */
    .status-group {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .badge {{
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
    }}
    .badge.pulse-green {{
      border-color: rgba(16, 185, 129, 0.5);
      color: #34d399;
    }}
    .badge.pulse-green::before {{
      content: '';
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green-bull);
      box-shadow: 0 0 8px var(--green-bull);
    }}
    .badge.pulse-warning {{
      border-color: rgba(245, 158, 11, 0.5);
      color: var(--gold-primary);
    }}
    .badge.pulse-warning::before {{
      content: '';
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--gold-primary);
      box-shadow: 0 0 8px var(--gold-primary);
    }}

    /* Action Controls */
    .controls {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .btn {{
      background: var(--bg-card);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      background: #334155;
      border-color: var(--gold-primary);
    }}
    .btn-gold {{
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #090d16;
      border: none;
      font-weight: 700;
    }}
    .btn-gold:hover {{
      background: linear-gradient(135deg, #fbbf24, #f59e0b);
      box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
    }}

    /* Main Workspace Layout */
    .workspace {{
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 380px;
      height: calc(100vh - 60px);
      overflow: hidden;
    }}

    /* Chart & Scanner Section */
    .chart-section {{
      display: flex;
      flex-direction: column;
      border-right: 1px solid var(--border-color);
      overflow: hidden;
      position: relative;
    }}

    /* Institutional HUD Bar */
    .hud-bar {{
      background: #0b1120;
      padding: 10px 16px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      font-size: 13px;
    }}
    .hud-stat {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .hud-label {{
      color: var(--text-muted);
      font-size: 11px;
      text-transform: uppercase;
    }}
    .hud-value {{
      font-weight: 700;
      color: #ffffff;
    }}
    .hud-score-meter {{
      width: 140px;
      height: 8px;
      background: #1e293b;
      border-radius: 4px;
      overflow: hidden;
      position: relative;
    }}
    .hud-score-fill {{
      height: 100%;
      width: 30%;
      background: var(--gold-primary);
      transition: width 0.5s ease;
    }}

    /* TradingView Chart Container */
    .tv-wrapper {{
      flex: 1;
      position: relative;
      background: var(--bg-dark);
      width: 100%;
      height: 100%;
    }}

    /* Signal Plan Drawer / Footer */
    .signal-footer {{
      background: var(--bg-panel);
      border-top: 1px solid var(--border-color);
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      min-height: 80px;
    }}
    .signal-pill {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .signal-tag {{
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 800;
      font-size: 14px;
      letter-spacing: 0.5px;
    }}
    .tag-wait {{
      background: rgba(148, 163, 184, 0.15);
      color: #94a3b8;
      border: 1px solid #475569;
    }}
    .tag-buy {{
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid var(--green-bull);
      box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }}
    .tag-sell {{
      background: rgba(239, 68, 68, 0.2);
      color: #f87171;
      border: 1px solid var(--red-bear);
      box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
    }}
    .signal-details {{
      display: flex;
      align-items: center;
      gap: 20px;
      font-size: 13px;
      flex-wrap: wrap;
    }}
    .detail-item {{
      display: flex;
      flex-direction: column;
    }}
    .detail-item .lbl {{
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
    }}
    .detail-item .val {{
      font-weight: 700;
      color: #ffffff;
      font-family: monospace;
      font-size: 14px;
    }}

    /* Chat & AI TradeDesk Assistant Panel */
    .assistant-section {{
      background: var(--bg-panel);
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }}
    .assistant-header {{
      padding: 14px 18px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .assistant-header h2 {{
      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .chat-messages {{
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .msg {{
      max-width: 88%;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 13px;
      line-height: 1.5;
      white-space: pre-wrap;
    }}
    .msg-bot {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      align-self: flex-start;
      color: #f1f5f9;
      border-left: 3px solid var(--gold-primary);
    }}
    .msg-user {{
      background: #2563eb;
      color: #ffffff;
      align-self: flex-end;
    }}

    /* Quick Prompts Chips */
    .quick-chips {{
      display: flex;
      gap: 6px;
      padding: 8px 16px;
      overflow-x: auto;
      background: #0b1120;
      border-top: 1px solid var(--border-color);
    }}
    .chip {{
      white-space: nowrap;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 11px;
      padding: 5px 10px;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .chip:hover {{
      color: var(--gold-primary);
      border-color: var(--gold-primary);
      background: #1e293b;
    }}

    /* Input Bar */
    .chat-input-bar {{
      padding: 12px 16px;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 8px;
      background: var(--bg-panel);
    }}
    .chat-input-bar input {{
      flex: 1;
      background: var(--bg-dark);
      border: 1px solid var(--border-color);
      color: #ffffff;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 13px;
      outline: none;
    }}
    .chat-input-bar input:focus {{
      border-color: var(--gold-primary);
    }}

    /* Modal / Popup */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(0,0,0,0.7);
      backdrop-filter: blur(4px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
    }}
    .modal-content {{
      background: var(--bg-panel);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      width: 90%;
      max-width: 600px;
      padding: 24px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .modal-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border-color);
    }}
    .modal-header h3 {{
      font-size: 16px;
      color: var(--gold-primary);
    }}
    .modal-close {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 20px;
      cursor: pointer;
    }}
    .modal-body {{
      font-size: 13px;
      line-height: 1.6;
      color: #cbd5e1;
      max-height: 60vh;
      overflow-y: auto;
    }}
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header>
    <div class="brand">
      <div class="brand-logo">AU</div>
      <div class="brand-text">
        <h1>GOLD SNIPER AI • TERMINAL</h1>
        <span>Ahmed's Institutional Desk</span>
      </div>
    </div>

    <!-- Live Status Indicators -->
    <div class="status-group">
      <div class="badge pulse-green" id="marketThreatBadge">
        <span id="marketThreatText">ForexFactory Radar: CLEAR</span>
      </div>
      <div class="badge" id="riskBadge" style="color: #94a3b8;">
        Balance: ${account_balance:,.2f} | Risk: {risk_percent}% (${account_balance * (risk_percent / 100):,.2f})
      </div>
      <div class="badge pulse-warning" id="botStatusBadge">
        Auto-Pilot: <strong id="autoPilotState">ACTIVE</strong>
      </div>
    </div>

    <!-- Actions & Quick Controls -->
    <div class="controls">
      <button class="btn btn-gold" onclick="triggerManualScan()">⚡ Scan Market Now</button>
      <button class="btn" onclick="openPredictionModal()">🔮 Prediction</button>
      <button class="btn" onclick="openNewsModal()">📰 News Radar</button>
      <button class="btn" onclick="simulateTestSignal()" title="Test audio & alert flow">🚨 Test Signal</button>
    </div>
  </header>

  <!-- Workspace: Chart + Assistant -->
  <div class="workspace">

    <!-- Chart & Institutional Confluence Section -->
    <div class="chart-section">
      <!-- HUD Confluence Bar -->
      <div class="hud-bar">
        <div class="hud-stat">
          <span class="hud-label">Pair:</span>
          <span class="hud-value" style="color: var(--gold-primary);">XAU/USD (Gold)</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">Confluence Score:</span>
          <div class="hud-score-meter">
            <div class="hud-score-fill" id="scoreBar" style="width: 30%;"></div>
          </div>
          <span class="hud-value" id="scoreVal">30%</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">Threshold:</span>
          <span class="hud-value">{min_confluence}% (Grade A+)</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">SMC Structure:</span>
          <span class="hud-value" id="smcStructureText" style="color: #38bdf8;">Monitoring FVGs & Sweeps</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">Last Checked:</span>
          <span class="hud-value" id="lastScanTime" style="color: #94a3b8; font-size: 11px;">Just now</span>
        </div>
      </div>

      <!-- Live TradingView Chart Widget (Official Advanced Real-Time Stream) -->
      <div class="tv-wrapper">
        <div class="tradingview-widget-container" style="height:100%;width:100%">
          <div id="tradingview_gold_chart" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
            new TradingView.widget({{
              "autosize": true,
              "symbol": "OANDA:XAUUSD",
              "interval": "15",
              "timezone": "Etc/UTC",
              "theme": "dark",
              "style": "1",
              "locale": "en",
              "enable_publishing": false,
              "backgroundColor": "#090d16",
              "gridColor": "#1e293b",
              "allow_symbol_change": true,
              "studies": [
                "STD;EMA",
                "STD;Average_True_Range"
              ],
              "container_id": "tradingview_gold_chart"
            }});
          </script>
        </div>
      </div>

      <!-- Live Signal & Lot Sizing Footer -->
      <div class="signal-footer">
        <div class="signal-pill">
          <div class="signal-tag tag-wait" id="signalBadge">WAITING (CONFLUENCE)</div>
          <div class="detail-item">
            <span class="lbl">Institutional Setup Status</span>
            <span class="val" id="signalReasonText" style="color: #94a3b8; font-size: 12px; font-weight: normal;">
              Bot scanning 15m Fair Value Gaps and Trend confluence. Preserving capital.
            </span>
          </div>
        </div>

        <div class="signal-details" id="planDetails">
          <div class="detail-item">
            <span class="lbl">Entry</span>
            <span class="val" id="planEntry">--</span>
          </div>
          <div class="detail-item">
            <span class="lbl">Stop Loss (ATR)</span>
            <span class="val" id="planSL" style="color: var(--red-bear);">--</span>
          </div>
          <div class="detail-item">
            <span class="lbl">TP1 (1:1.5 RR)</span>
            <span class="val" id="planTP1" style="color: var(--green-bull);">--</span>
          </div>
          <div class="detail-item">
            <span class="lbl">TP2 (1:3.0 RR)</span>
            <span class="val" id="planTP2" style="color: var(--green-bull);">--</span>
          </div>
          <div class="detail-item">
            <span class="lbl">Rec. Lot Size</span>
            <span class="val" id="planLot" style="color: var(--gold-primary);">1.0 Lots</span>
          </div>
        </div>
      </div>
    </div>

    <!-- AI TradeDesk Assistant (Side-by-Side with Chart) -->
    <div class="assistant-section">
      <div class="assistant-header">
        <h2>💬 TradeDesk AI • {user_name}</h2>
        <span class="badge" style="background:#0b1120; font-size: 11px;">Active Partner</span>
      </div>

      <div class="chat-messages" id="chatMessages">
        <div class="msg msg-bot">Hey {user_name}! I am watching the live Gold chart alongside you.

Ask me to review a trade idea, calculate your lot size, check upcoming CPI/NFP news, or give you our institutional prediction!</div>
      </div>

      <!-- Quick Action Chips -->
      <div class="quick-chips">
        <div class="chip" style="color: var(--gold-primary); font-weight: bold; border-color: var(--gold-primary);" onclick="sendQuickPrompt('Give me a live trade signal on Gold right now')">⚡ Give Me A Signal</div>
        <div class="chip" onclick="sendQuickPrompt('What is Gold doing right now?')">📊 Gold Trend</div>
        <div class="chip" onclick="sendQuickPrompt('Calculate lot size for balance 10000 risk 1% entry 2685 SL 2679')">📐 Calc Lots</div>
        <div class="chip" onclick="sendQuickPrompt('Will Gold crash tomorrow? Show me the market prediction')">🔮 Crash Outlook</div>
        <div class="chip" onclick="sendQuickPrompt('When is the next high impact CPI or NFP news?')">📰 CPI/NFP News</div>
        <div class="chip" onclick="sendQuickPrompt('Explain Fair Value Gaps (FVG) and how to trade them')">📚 Explain FVG</div>
      </div>

      <!-- Input Bar -->
      <div class="chat-input-bar">
        <input type="text" id="chatInput" placeholder="Ask about a trade, CPI news, lot size..." onkeydown="if(event.key==='Enter') sendChatMessage()">
        <button class="btn btn-gold" onclick="sendChatMessage()">Send</button>
      </div>
    </div>

  </div>

  <!-- Modal: Market Prediction -->
  <div class="modal-overlay" id="predictionModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3 id="predTitle">🔮 Forward-Looking Market Prediction</h3>
        <button class="modal-close" onclick="closePredictionModal()">&times;</button>
      </div>
      <div class="modal-body" id="predBody">
        Loading predictive macro outlook...
      </div>
    </div>
  </div>

  <!-- Modal: News Radar -->
  <div class="modal-overlay" id="newsModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>📰 ForexFactory Economic News Radar</h3>
        <button class="modal-close" onclick="closeNewsModal()">&times;</button>
      </div>
      <div class="modal-body" id="newsBody">
        Loading economic calendar...
      </div>
    </div>
  </div>

  <!-- Application Logic -->
  <script>
    // Audio Chime Generator using Web Audio API (Zero external assets required)
    function playInstitutionalAlertChime(isBuy = true) {{
      try {{
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = 'sine';
        osc.frequency.setValueAtTime(isBuy ? 587.33 : 440.0, ctx.currentTime); // D5 or A4
        osc.frequency.exponentialRampToValueAtTime(isBuy ? 880.0 : 329.63, ctx.currentTime + 0.3);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
        osc.start();
        osc.stop(ctx.currentTime + 0.6);
      }} catch(e) {{
        console.log("Audio alert suppressed or unavailable:", e);
      }}
    }}

    // Manual or Auto-Pilot Scan
    async function triggerManualScan() {{
      const hudScore = document.getElementById('scoreVal');
      const scoreBar = document.getElementById('scoreBar');
      const timeElem = document.getElementById('lastScanTime');
      const signalBadge = document.getElementById('signalBadge');
      const reasonText = document.getElementById('signalReasonText');
      const smcText = document.getElementById('smcStructureText');

      timeElem.textContent = 'Scanning...';

      try {{
        const res = await fetch('/api/scan', {{ method: 'POST' }});
        const data = await res.json();
        
        const score = data.confluence_score || 0;
        hudScore.textContent = score + '%';
        scoreBar.style.width = Math.min(score, 100) + '%';
        timeElem.textContent = new Date().toLocaleTimeString();

        if (data.signal === 'BUY') {{
          signalBadge.className = 'signal-tag tag-buy';
          signalBadge.textContent = '🟢 GRADE A+ BUY';
          reasonText.textContent = data.reason || 'High Confluence SMC Buy Triggered';
          smcText.textContent = 'Bullish Trend + FVG Rejection Confirmed';
          smcText.style.color = '#34d399';
          playInstitutionalAlertChime(true);
          updatePlanUI(data.trade_plan);
        }} else if (data.signal === 'SELL') {{
          signalBadge.className = 'signal-tag tag-sell';
          signalBadge.textContent = '🔴 GRADE A+ SELL';
          reasonText.textContent = data.reason || 'High Confluence SMC Sell Triggered';
          smcText.textContent = 'Bearish Trend + Liquidity Sweep Confirmed';
          smcText.style.color = '#f87171';
          playInstitutionalAlertChime(false);
          updatePlanUI(data.trade_plan);
        }} else if (data.signal === 'LOCKOUT') {{
          signalBadge.className = 'signal-tag tag-wait';
          signalBadge.textContent = '⚠️ NEWS LOCKOUT';
          reasonText.textContent = data.reason || 'High-impact USD event within freeze window.';
          smcText.textContent = 'Entries Frozen (Capital Protection)';
          smcText.style.color = '#f59e0b';
        }} else {{
          signalBadge.className = 'signal-tag tag-wait';
          signalBadge.textContent = 'WAITING (CONFLUENCE)';
          reasonText.textContent = data.reason || 'No Grade A+ setup currently. Preserving capital.';
          smcText.textContent = 'Monitoring FVGs & Sweeps';
          smcText.style.color = '#38bdf8';
        }}
      }} catch (err) {{
        timeElem.textContent = 'Scan error';
        console.error(err);
      }}
    }}

    function updatePlanUI(plan) {{
      if (!plan) return;
      document.getElementById('planEntry').textContent = '$' + (plan.entry_price || '--');
      document.getElementById('planSL').textContent = '$' + (plan.stop_loss || '--');
      document.getElementById('planTP1').textContent = '$' + (plan.tp1 || '--');
      document.getElementById('planTP2').textContent = '$' + (plan.tp2 || '--');
      document.getElementById('planLot').textContent = (plan.recommended_lot_size || '1.0') + ' Lots';
    }}

    // Simulation for Ahmed to test alert flow
    function simulateTestSignal() {{
      const signalBadge = document.getElementById('signalBadge');
      const scoreBar = document.getElementById('scoreBar');
      const hudScore = document.getElementById('scoreVal');
      const smcText = document.getElementById('smcStructureText');
      const reasonText = document.getElementById('signalReasonText');

      hudScore.textContent = '92%';
      scoreBar.style.width = '92%';
      signalBadge.className = 'signal-tag tag-buy';
      signalBadge.textContent = '🟢 GRADE A+ BUY';
      reasonText.textContent = 'Liquidity Sweep of Asian Low ($2682) + Bullish Fair Value Gap + 200 EMA Support';
      smcText.textContent = '92% Confluence Confirmed (Grade A+)';
      smcText.style.color = '#34d399';

      updatePlanUI({{
        entry_price: 2686.50,
        stop_loss: 2680.50,
        tp1: 2695.50,
        tp2: 2704.50,
        recommended_lot_size: 1.6
      }});

      playInstitutionalAlertChime(true);

      // Add notification in chat
      addBotChatMessage('🚨 [SIMULATED GRADE A+ BUY DETECTED]\\n\\nEntry: $2686.50\\nSL: $2680.50 (-$6.00)\\nTP1: $2695.50 (1:1.5 RR)\\nTP2: $2704.50 (1:3.0 RR)\\nRecommended Lot: 1.6 Lots (1.0% Risk)');
    }}

    // Chat Functions
    async function sendChatMessage() {{
      const input = document.getElementById('chatInput');
      const text = input.value.trim();
      if (!text) return;

      addUserChatMessage(text);
      input.value = '';

      try {{
        const res = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ message: text }})
        }});
        const data = await res.json();
        addBotChatMessage(data.response);
      }} catch (e) {{
        addBotChatMessage("Error connecting to trade desk AI. Please check server status.");
      }}
    }}

    function sendQuickPrompt(promptText) {{
      addUserChatMessage(promptText);
      fetch('/api/chat', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: promptText }})
      }})
      .then(res => res.json())
      .then(data => addBotChatMessage(data.response));
    }}

    function addUserChatMessage(msg) {{
      const container = document.getElementById('chatMessages');
      const div = document.createElement('div');
      div.className = 'msg msg-user';
      div.textContent = msg;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }}

    function addBotChatMessage(msg) {{
      const container = document.getElementById('chatMessages');
      const div = document.createElement('div');
      div.className = 'msg msg-bot';
      div.textContent = msg;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }}

    // Modals
    async function openPredictionModal() {{
      const modal = document.getElementById('predictionModal');
      const body = document.getElementById('predBody');
      modal.style.display = 'flex';
      body.innerHTML = 'Analyzing macro catalysts, liquidity pockets, and crash risk...';

      try {{
        const res = await fetch('/api/prediction?symbol=XAUUSD');
        const data = await res.json();
        body.innerHTML = `
          <div style="margin-bottom: 12px; font-weight: bold; font-size: 15px; color: #f59e0b;">${{data.headline}}</div>
          <p style="margin-bottom: 10px;"><strong>Directional Bias:</strong> <span style="color: #38bdf8;">${{data.directional_bias}}</span></p>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
            <div style="background: #1e293b; padding: 10px; border-radius: 6px;">
              <span style="font-size: 11px; color: #94a3b8;">Crash Probability</span>
              <div style="font-size: 16px; font-weight: bold; color: #f87171;">${{data.crash_risk_probability}}</div>
            </div>
            <div style="background: #1e293b; padding: 10px; border-radius: 6px;">
              <span style="font-size: 11px; color: #94a3b8;">Rally Probability</span>
              <div style="font-size: 16px; font-weight: bold; color: #34d399;">${{data.rally_probability}}</div>
            </div>
          </div>
          <p style="margin-bottom: 8px;"><strong>Macro Catalyst:</strong> ${{data.macro_catalyst}}</p>
          <p style="margin-bottom: 8px;"><strong>Invalidation Level:</strong> $${{data.invalidation_level}}</p>
          <div style="background: #0f172a; border-left: 3px solid #f59e0b; padding: 10px; margin-top: 12px; font-size: 12px;">
            <strong>Institutional Summary:</strong> ${{data.actionable_summary}}
          </div>
        `;
      }} catch (e) {{
        body.innerHTML = 'Unable to fetch prediction at this time.';
      }}
    }}

    function closePredictionModal() {{
      document.getElementById('predictionModal').style.display = 'none';
    }}

    async function openNewsModal() {{
      const modal = document.getElementById('newsModal');
      const body = document.getElementById('newsBody');
      modal.style.display = 'flex';
      body.innerHTML = 'Querying ForexFactory economic calendar...';

      try {{
        const res = await fetch('/api/news');
        const data = await res.json();
        const threat = data.threat || {{}};
        const events = data.events || [];

        let html = `
          <div style="padding: 10px; background: #1e293b; border-radius: 6px; margin-bottom: 14px;">
            <strong>News Status:</strong> <span style="color: #34d399;">${{threat.status || 'CLEAR'}}</span><br>
            <span style="font-size: 12px; color: #94a3b8;">${{threat.reason || 'No immediate Tier-1 economic shocks.'}}</span>
          </div>
          <h4 style="margin-bottom: 8px; color: #f59e0b;">Upcoming Tier-1 Releases (Next 72h):</h4>
        `;

        if (events.length === 0) {{
          html += '<p style="color: #94a3b8;">No high-impact USD events scheduled in the next 72 hours.</p>';
        }} else {{
          html += '<div style="display:flex; flex-direction:column; gap:8px;">';
          events.slice(0, 5).forEach(e => {{
            html += `
              <div style="background: #090d16; border: 1px solid #334155; padding: 8px 12px; border-radius: 6px; font-size: 12px;">
                <div style="font-weight: bold; color: #ffffff;">[${{e.country}}] ${{e.title}}</div>
                <div style="color: #94a3b8; font-size: 11px;">Time: ${{e.date}} | Exp: ${{e.forecast || 'N/A'}} | Prev: ${{e.previous || 'N/A'}}</div>
              </div>
            `;
          }});
          html += '</div>';
        }}
        body.innerHTML = html;
      }} catch (e) {{
        body.innerHTML = 'Unable to fetch ForexFactory events.';
      }}
    }}

    function closeNewsModal() {{
      document.getElementById('newsModal').style.display = 'none';
    }}

    // Auto-Pilot Background Loop (every 30 seconds)
    setInterval(() => {{
      triggerManualScan();
    }}, 30000);

    // Initial scan on load
    window.addEventListener('load', () => {{
      triggerManualScan();
    }});
  </script>
</body>
</html>
"""
