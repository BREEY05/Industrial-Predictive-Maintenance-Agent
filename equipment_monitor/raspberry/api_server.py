from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import threading
import asyncio

# 导入数据模拟器模块
from . import data_simulator

# ─────────────────────────────────────────
# 配置 (部分配置项将从外部传入或在 config.py 中定义)
# ─────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
OLLAMA_HOST = "http://192.168.43.105:11434" # 默认值，可由前端设置
OLLAMA_MODEL = "qwen3:4b" # 默认值

# 自动提交结果队列（前端轮询取走）
auto_results_for_frontend = []
auto_results_for_frontend_lock = threading.Lock()

def add_auto_result_for_frontend(result: dict):
    """添加自动提交结果到队列，供前端轮询"""
    with auto_results_for_frontend_lock:
        auto_results_for_frontend.append(result)

def pop_auto_result_for_frontend():
    """从队列中取出自动提交结果，供前端轮询"""
    with auto_results_for_frontend_lock:
        if auto_results_for_frontend:
            return auto_results_for_frontend.pop(0)
    return None

# ─────────────────────────────────────────
# FastAPI 应用
# ─────────────────────────────────────────
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/simulate")
def simulate():
    data_simulator.add_record()
    return JSONResponse({"status": "ok", "data": data_simulator.get_current_stats()["latest"]})

@app.get("/api/stats")
def get_stats():
    return data_simulator.get_current_stats()

@app.get("/api/poll_auto")
def poll_auto():
    """前端轮询：取走自动提交结果"""
    result = pop_auto_result_for_frontend()
    if result:
        return JSONResponse({"has_result": True, **result})
    return JSONResponse({"has_result": False})

@app.post("/api/analyze")
async def analyze():
    # 此处不再直接执行分析，而是通知 agent 端进行分析
    # 或者，如果 agent 端是独立的，这里可以触发一个异步任务
    # 暂时保留原有的 do_analyze 逻辑，但未来会移除
    return JSONResponse({"status": "error", "message": "分析功能已移至 Agent 端"})

@app.post("/api/set_threshold")
async def set_threshold(body: dict):
    new_config = data_simulator.update_threshold_config(body)
    return JSONResponse({"status": "ok", "threshold": new_config})

@app.post("/api/chat")
async def chat(body: dict):
    user_msg = body.get("message", "")
    if not user_msg:
        return JSONResponse({"status": "error", "reply": "消息不能为空"})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": f"你是工业设备维护专家助手，请用中文回答：{user_msg}", "stream": False}
            )
            result = response.json()
            return JSONResponse({"status": "ok", "reply": result.get("response", "")})
    except Exception as e:
        return JSONResponse({"status": "error", "reply": f"❌ 请求失败: {str(e)}"})

@app.get("/api/set_ollama")
def set_ollama(ip: str):
    global OLLAMA_HOST
    OLLAMA_HOST = f"http://{ip}:11434"
    return JSONResponse({"status": "ok", "ollama_host": OLLAMA_HOST})

@app.get("/", response_class=HTMLResponse)
def dashboard():
    html = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>工业设备监控仪表盘</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #0f1117; color: #e0e0e0; padding: 24px; }
        h1 { font-size: 22px; margin-bottom: 8px; color: #fff; }
        .subtitle { font-size: 13px; color: #888; margin-bottom: 20px; }
        .stats { display: flex; gap: 16px; margin-bottom: 20px; }
        .stat { background: #1c1f2e; border-radius: 8px; padding: 16px 24px; flex: 1; text-align: center; }
        .stat .num { font-size: 32px; font-weight: bold; }
        .stat .lbl { font-size: 13px; color: #888; margin-top: 4px; }
        .cards { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
        .card { background: #1c1f2e; border-radius: 8px; padding: 16px 24px; flex: 1; min-width: 120px; text-align: center; }
        .card .label { font-size: 12px; color: #888; margin-bottom: 6px; }
        .card .value { font-size: 24px; font-weight: bold; }
        .config-panel { background: #1c1f2e; border-radius: 10px; padding: 16px; margin-bottom: 20px; border: 1px solid #2d3147; }
        .config-panel h3 { font-size: 14px; color: #aaa; margin-bottom: 12px; }
        .config-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
        .config-row label { font-size: 13px; color: #888; min-width: 120px; }
        .config-input { background: #252837; border: 1px solid #3d4160; border-radius: 6px; color: #e0e0e0; padding: 5px 10px; font-size: 13px; width: 80px; }
        .config-btn { background: #1677ff; border: none; border-radius: 6px; color: #fff; padding: 6px 14px; cursor: pointer; font-size: 13px; }
        .config-btn:hover { background: #4096ff; }
        .switch { position: relative; width: 42px; height: 22px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; inset: 0; background: #3d4160; border-radius: 22px; transition: .3s; }
        .slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: .3s; }
        input:checked + .slider { background: #1677ff; }
        input:checked + .slider:before { transform: translateX(20px); }
        .threshold-bar { background: #252837; border-radius: 6px; height: 8px; margin-top: 6px; overflow: hidden; }
        .threshold-fill { height: 100%; border-radius: 6px; background: #fa8c16; transition: width 0.3s; }
        .btns { display: flex; gap: 12px; margin-bottom: 20px; }
        .btn { flex: 1; padding: 16px; font-size: 16px; font-weight: bold; border: none; border-radius: 10px; cursor: pointer; }
        .btn-sim { background: #fa8c16; color: #fff; }
        .btn-sim:hover { background: #ffa940; }
        .btn-submit { background: #1677ff; color: #fff; }
        .btn-submit:hover { background: #4096ff; }
        .btn:active { transform: scale(0.97); }
        .pending-badge { background: #ff4d4f; color: #fff; border-radius: 12px; padding: 2px 8px; font-size: 12px; margin-left: 8px; }
        h2 { font-size: 16px; margin-bottom: 12px; color: #ccc; }
        table { width: 100%; border-collapse: collapse; background: #1c1f2e; border-radius: 8px; overflow: hidden; margin-bottom: 80px; }
        th { background: #252837; padding: 10px 14px; text-align: left; font-size: 13px; color: #aaa; }
        td { padding: 10px 14px; font-size: 13px; border-top: 1px solid #252837; }
        #ip-bar { background: #1c1f2e; border: 1px solid #2d3147; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; font-size: 13px; flex-wrap: wrap; }
        #ip-input { background: #252837; border: 1px solid #3d4160; border-radius: 6px; color: #e0e0e0; padding: 5px 10px; font-size: 13px; width: 150px; }
        #ip-btn { background: #1677ff; border: none; border-radius: 6px; color: #fff; padding: 5px 12px; cursor: pointer; font-size: 13px; }
        #ip-status { color: #52c41a; font-size: 12px; }
        #ai-fab { position: fixed; bottom: 28px; right: 28px; width: 56px; height: 56px; background: #1677ff; border-radius: 50%; border: none; cursor: pointer; font-size: 24px; color: #fff; box-shadow: 0 4px 16px rgba(22,119,255,0.4); z-index: 100; transition: transform 0.2s; }
        #ai-fab:hover { background: #4096ff; transform: scale(1.08); }
        #ai-fab.has-notify { background: #ff4d4f; animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(255,77,79,0.4)} 50%{box-shadow:0 0 0 10px rgba(255,77,79,0)} }
        #ai-panel { position: fixed; bottom: 96px; right: 28px; width: 380px; height: 520px; background: #1c1f2e; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); display: none; flex-direction: column; z-index: 99; border: 1px solid #2d3147; }
        #ai-panel.open { display: flex; }
        #ai-header { padding: 14px 16px; background: #252837; border-radius: 16px 16px 0 0; font-weight: bold; font-size: 14px; display: flex; justify-content: space-between; align-items: center; }
        #ai-close { background: none; border: none; color: #888; cursor: pointer; font-size: 18px; }
        #ai-messages { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
        .msg { max-width: 88%; padding: 10px 13px; border-radius: 12px; font-size: 13px; line-height: 1.5; white-space: pre-wrap; }
        .msg.user { background: #1677ff; color: #fff; align-self: flex-end; border-radius: 12px 12px 2px 12px; }
        .msg.ai { background: #252837; color: #e0e0e0; align-self: flex-start; border-radius: 12px 12px 12px 2px; }
        .msg.sys { background: #1a2035; color: #888; align-self: center; font-size: 12px; border-radius: 8px; }
        .msg.auto-trigger { background: #3d0a0a; color: #ff4d4f; align-self: center; font-size: 12px; border-radius: 8px; border: 1px solid #ff4d4f44; }
        #ai-input-area { padding: 10px; border-top: 1px solid #2d3147; display: flex; gap: 8px; }
        #ai-input { flex: 1; background: #252837; border: 1px solid #3d4160; border-radius: 8px; color: #e0e0e0; padding: 8px 12px; font-size: 13px; resize: none; height: 38px; }
        #ai-send { background: #1677ff; border: none; border-radius: 8px; color: #fff; padding: 8px 14px; cursor: pointer; font-size: 13px; }
        .dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#52c41a; margin-right:5px; animation: blink 1s infinite; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
    </style>
</head>
<body>
    <h1>🏭 工业设备预测性维护系统</h1>
    <p class="subtitle"><span class="dot"></span>实时监控 · 自动刷新</p>

    <div id="ip-bar">
        🔗 Ollama IP：
        <input id="ip-input" type="text" placeholder="192.168.43.105" value="192.168.43.105"/>
        <button id="ip-btn" onclick="setOllamaIP()">确认</button>
        <span id="ip-status"></span>
    </div>

    <div class="config-panel">
        <h3>⚙️ 阈值与模拟配置</h3>
        <div class="config-row">
            <label>异常概率</label>
            <input class="config-input" id="cfg-ratio" type="number" min="0" max="1" step="0.1" value="0.5"/>
            <span style="font-size:13px;color:#888;">（0~1，每次模拟生成异常的概率）</span>
        </div>
        <div class="config-row">
            <label>自动提交阈值</label>
            <input class="config-input" id="cfg-threshold" type="number" min="1" max="50" value="3"/>
            <span style="font-size:13px;color:#888;">条异常数据时自动提交AI分析</span>
        </div>
        <div class="config-row">
            <label>自动提交</label>
            <div style="display:flex;align-items:center;gap:8px;">
                <label class="switch">
                    <input type="checkbox" id="cfg-auto" checked>
                    <span class="slider"></span>
                </label>
                <span id="auto-label" style="font-size:13px;color:#52c41a;">开启</span>
            </div>
        </div>
        <div class="config-row">
            <button class="config-btn" onclick="saveConfig()">保存配置</button>
            <span id="cfg-status" style="font-size:12px;color:#52c41a;"></span>
        </div>
        <div style="margin-top:8px;">
            <div style="font-size:12px;color:#888;margin-bottom:4px;">待提交异常进度：<span id="pending-text">0 / 3</span></div>
            <div class="threshold-bar"><div class="threshold-fill" id="threshold-fill" style="width:0%"></div></div>
        </div>
    </div>

    <div class="stats">
        <div class="stat"><div class="num" id="total">-</div><div class="lbl">总记录数</div></div>
        <div class="stat"><div class="num" id="normal-count" style="color:#52c41a;">-</div><div class="lbl">正常次数</div></div>
        <div class="stat"><div class="num" id="anomaly-count" style="color:#ff4d4f;">-</div><div class="lbl">异常次数</div></div>
    </div>

    <div class="btns">
        <button class="btn btn-sim" onclick="simulate()">⚡ 模拟数据输入</button>
        <button class="btn btn-submit" onclick="submitAnalyze()">
            📤 提交分析 <span id="pending-badge" class="pending-badge" style="display:none;">0</span>
        </button>
    </div>

    <h2>📊 最新数据</h2>
    <div id="latest-cards"><p style="color:#888;margin-bottom:24px;">暂无数据</p></div>

    <h2>📋 最近记录（最新10条）</h2>
    <table>
        <thead><tr><th>时间戳</th><th>电流(A)</th><th>温度(°C)</th><th>振动(mm/s)</th><th>状态</th></tr></thead>
        <tbody id="tbody"><tr><td colspan="5" style="text-align:center;color:#888;">暂无数据</td></tr></tbody>
    </table>

    <button id="ai-fab" onclick="toggleAI()" title="AI助手">🤖</button>
    <div id="ai-panel">
        <div id="ai-header">
            🤖 AI设备维护助手
            <button id="ai-close" onclick="toggleAI()">✕</button>
        </div>
        <div id="ai-messages">
            <div class="msg sys">👋 点击「提交分析」发送设备数据，或直接输入问题对话</div>
        </div>
        <div id="ai-input-area">
            <textarea id="ai-input" placeholder="输入问题..." onkeydown="handleKey(event)"></textarea>
            <button id="ai-send" onclick="sendChat()">发送</button>
        </div>
    </div>

    <script>
        let aiOpen = false;

        function toggleAI() {
            aiOpen = !aiOpen;
            document.getElementById('ai-panel').classList.toggle('open', aiOpen);
            if (aiOpen) {
                // 打开时清除红点
                document.getElementById('ai-fab').classList.remove('has-notify');
            }
        }

        function addMsg(content, role) {
            const box = document.getElementById('ai-messages');
            const div = document.createElement('div');
            div.className = 'msg ' + role;
            div.textContent = content;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
            return div;
        }

        function handleKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
        }

        async function simulate() {
            await fetch('/api/simulate', {method: 'POST'});
        }

        async function submitAnalyze() {
            if (!aiOpen) toggleAI();
            const sys = addMsg('📤 正在提交设备数据进行分析...', 'sys');
            const typing = addMsg('⏳ AI分析中，请稍候...', 'sys');
            const res = await fetch('/api/analyze', {method: 'POST'});
            const d = await res.json();
            typing.remove();
            sys.remove();
            if (d.status === 'no_data') {
                addMsg('⚠️ 没有待分析数据，请先点击「模拟数据输入」', 'sys');
                return;
            }
            addMsg(`📊 已提交 ${d.analyzed_count} 条数据（其中异常 ${d.anomaly_count} 条）`, 'sys');
            addMsg(d.reply, 'ai');
        }

        async function sendChat() {
            const input = document.getElementById('ai-input');
            const msg = input.value.trim();
            if (!msg) return;
            input.value = '';
            addMsg(msg, 'user');
            const typing = addMsg('⏳ 思考中...', 'sys');
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const d = await res.json();
                typing.remove();
                addMsg(d.reply, 'ai');
            } catch(e) {
                typing.remove();
                addMsg('❌ 请求失败', 'ai');
            }
        }

        async function setOllamaIP() {
            const ip = document.getElementById('ip-input').value.trim();
            if (!ip) return;
            const res = await fetch('/api/set_ollama?ip=' + encodeURIComponent(ip));
            const d = await res.json();
            document.getElementById('ip-status').textContent = '✅ 已设置: ' + d.ollama_host;
        }

        async function saveConfig() {
            const ratio = parseFloat(document.getElementById('cfg-ratio').value);
            const threshold = parseInt(document.getElementById('cfg-threshold').value);
            const auto = document.getElementById('cfg-auto').checked;
            document.getElementById('auto-label').textContent = auto ? '开启' : '关闭';
            document.getElementById('auto-label').style.color = auto ? '#52c41a' : '#888';
            await fetch('/api/set_threshold', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({anomaly_count: threshold, auto_submit: auto, anomaly_ratio: ratio})
            });
            const s = document.getElementById('cfg-status');
            s.textContent = '✅ 已保存';
            setTimeout(() => s.textContent = '', 2000);
        }

        // 轮询自动提交结果（与loadStats分开，互不干扰）
        async function pollAutoResult() {
            try {
                const res = await fetch('/api/poll_auto');
                const d = await res.json();
                if (d.has_result) {
                    // 弹出AI面板
                    if (!aiOpen) {
                        toggleAI();
                    }
                    addMsg(`🚨 异常数达到阈值，已自动提交！\n分析 ${d.analyzed_count} 条数据（异常 ${d.anomaly_count} 条）`, 'auto-trigger');
                    addMsg(d.reply, 'ai');
                    // 如果面板未打开，给悬浮按钮加红点提示
                    if (!aiOpen) {
                        document.getElementById('ai-fab').classList.add('has-notify');
                    }
                }
            } catch(e) {}
        }

        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const d = await res.json();

                document.getElementById('total').textContent = d.total;
                document.getElementById('normal-count').textContent = d.normal;
                document.getElementById('anomaly-count').textContent = d.anomaly;

                // 进度条（使用前端当前阈值，不覆盖用户输入）
                const cfgThreshold = parseInt(document.getElementById('cfg-threshold').value) || d.threshold.anomaly_count;
                const pa = d.pending_anomaly || 0;
                const pct = Math.min(100, (pa / cfgThreshold) * 100);
                document.getElementById('pending-text').textContent = `${pa} / ${cfgThreshold}`;
                document.getElementById('threshold-fill').style.width = pct + '%';
                document.getElementById('threshold-fill').style.background = pct >= 100 ? '#ff4d4f' : '#fa8c16';

                // badge
                const badge = document.getElementById('pending-badge');
                if (d.pending_count > 0) { badge.style.display = 'inline'; badge.textContent = d.pending_count; }
                else { badge.style.display = 'none'; }

                // 最新数据卡片
                const latestDiv = document.getElementById('latest-cards');
                if (d.latest) {
                    const s = d.latest['状态'];
                    const c = s === '异常' ? '#ff4d4f' : '#52c41a';
                    latestDiv.innerHTML = `<div class="cards">
                        <div class="card"><div class="label">电流</div><div class="value">${d.latest['电流(A)']} A</div></div>
                        <div class="card"><div class="label">温度</div><div class="value">${d.latest['温度(°C)']} °C</div></div>
                        <div class="card"><div class="label">振动</div><div class="value">${d.latest['振动(mm/s)']} mm/s</div></div>
                        <div class="card"><div class="label">状态</div><div class="value" style="color:${c};">${s}</div></div>
                    </div>`;
                } else {
                    latestDiv.innerHTML = '<p style="color:#888;margin-bottom:24px;">暂无数据</p>';
                }

                // 表格
                const tbody = document.getElementById('tbody');
                if (d.recent && d.recent.length > 0) {
                    tbody.innerHTML = d.recent.map(r => {
                        const s = r['状态'];
                        const c = s === '异常' ? '#ff4d4f' : '#52c41a';
                        return `<tr>
                            <td>${r['时间戳']||'-'}</td>
                            <td>${r['电流(A)']||'-'}</td>
                            <td>${r['温度(°C)']||'-'}</td>
                            <td>${r['振动(mm/s)']||'-'}</td>
                            <td style="color:${c};font-weight:bold;">${s}</td>
                        </tr>`;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#888;">暂无数据</td></tr>';
                }
            } catch(e) { console.error('刷新失败', e); }
        }

        loadStats();
        setInterval(loadStats, 1000);
        setInterval(pollAutoResult, 1500);  // 每1.5秒轮询一次自动提交结果
    </script>
</body>
</html>"""
    return html

# if __name__ == "__main__":
#     print("=" * 50)
#     print("🏭 工业设备预测性维护系统 - 树莓派端")
#     print("=" * 50)
#     print(f"📡 Web: http://0.0.0.0:{API_PORT}")
#     print(f"🤖 Ollama: {OLLAMA_HOST}  模型: {OLLAMA_MODEL}")
#     print(f"📝 提交日志: {SUBMIT_LOG_PATH}")
#     print("=" * 50)
#     uvicorn.run(app, host=API_HOST, port=API_PORT)
