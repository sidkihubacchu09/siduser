// --- Global State ---
const AppState = {
    phone: '',
    scriptContent: '',
    activeBots: {} 
};

// --- Toast Notifications ---
const toast = {
    show(message, type = 'success') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;';
            document.body.appendChild(container);
        }
        const element = document.createElement('div');
        const bgColor = type === 'error' ? 'rgba(255, 95, 86, 0.9)' : 'rgba(39, 201, 63, 0.9)';
        element.style.cssText = `background: ${bgColor}; color: #fff; padding: 14px 24px; border-radius: 12px; font-size: 0.95rem; backdrop-filter: blur(10px); transition: 0.3s; opacity:0; transform:translateY(10px);`;
        element.innerText = message;
        container.appendChild(element);
        
        requestAnimationFrame(() => { element.style.opacity = '1'; element.style.transform = 'translateY(0)'; });
        setTimeout(() => { element.style.opacity = '0'; setTimeout(() => element.remove(), 300); }, 4000);
    }
};

// --- Navigation ---
const nav = {
    switchTab(targetViewId, element) {
        document.querySelectorAll('.view-section').forEach(view => view.classList.add('hidden'));
        document.getElementById(targetViewId).classList.remove('hidden');
        document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
        if (element) element.classList.add('active');
    }
};

// --- UI Engine (Video Background) ---
window.updateBackgroundFromSettings = function() {
    const url = document.getElementById('video-url-input').value.trim();
    const videoElement = document.getElementById('bg-video');
    if (videoElement && url) {
        videoElement.src = url;
        videoElement.load();
        videoElement.play().catch(() => {});
        toast.show('Background updated successfully.', 'success');
    }
};

// --- Deployment Flow (API Connected) ---
const deployFlow = {
    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('scriptInput').value = e.target.result;
            document.getElementById('filename-display').innerText = file.name;
            toast.show(`File ${file.name} loaded.`);
        };
        reader.readAsText(file);
    },

    async nextToOTP() {
        const phone = document.getElementById('phoneInput').value.trim();
        const script = document.getElementById('scriptInput').value.trim();
        const btn = document.getElementById('btn-deploy');

        if (!phone || !script) return toast.show('Phone and script are required.', 'error');
        AppState.phone = phone;
        btn.classList.add('loading');

        try {
            const res = await fetch('/api/deploy/initiate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, script: script })
            });
            const data = await res.json();
            btn.classList.remove('loading');

            if (data.status === 'awaiting_otp') {
                document.getElementById('otp-phone-display').innerText = `Code sent to ${phone}.`;
                this.goBack('step1-script', 'step2-otp');
                toast.show('Request sent. Waiting for OTP.');
            } else {
                toast.show(data.message || 'Error', 'error');
            }
        } catch (e) {
            btn.classList.remove('loading');
            toast.show('Network error.', 'error');
        }
    },

    async nextToPassword() {
        const otpCode = document.getElementById('otpInput').value.trim();
        const btn = document.getElementById('btn-otp');
        if (!otpCode) return toast.show('Enter OTP.', 'error');
        btn.classList.add('loading');

        try {
            const res = await fetch('/api/deploy/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: AppState.phone, code: otpCode })
            });
            const data = await res.json();
            btn.classList.remove('loading');

            if (data.status === 'awaiting_2fa') {
                this.goBack('step2-otp', 'step3-password');
                toast.show('2FA Required.');
            } else if (data.status === 'deployed') {
                this.success();
            } else {
                toast.show(data.message || 'Verification failed.', 'error');
            }
        } catch (e) {
            btn.classList.remove('loading');
            toast.show('Network error.', 'error');
        }
    },

    async finalize() {
        const password = document.getElementById('passwordInput').value;
        const btn = document.getElementById('btn-pass');
        if (!password) return toast.show('Enter 2FA Password.', 'error');
        btn.classList.add('loading');

        try {
            const res = await fetch('/api/deploy/finalize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: AppState.phone, password: password })
            });
            const data = await res.json();
            btn.classList.remove('loading');

            if (data.status === 'deployed') {
                this.success();
            } else {
                toast.show(data.message || 'Incorrect Password.', 'error');
            }
        } catch (e) {
            btn.classList.remove('loading');
            toast.show('Network error.', 'error');
        }
    },

    success() {
        document.getElementById('step2-otp').classList.add('hidden');
        document.getElementById('step3-password').classList.add('hidden');
        document.getElementById('step4-success').classList.remove('hidden');
        
        const fileName = document.getElementById('filename-display').innerText;
        const safeId = AppState.phone.replace(/[^0-9]/g, ''); 
        
        AppState.activeBots[safeId] = { phoneKey: AppState.phone, name: fileName, status: 'Running' };
        this.renderBots();
        toast.show('Userbot Successfully Deployed!', 'success');
    },

    goBack(hideId, showId) {
        document.getElementById(hideId).classList.add('hidden');
        document.getElementById(showId).classList.remove('hidden');
    },

    reset() {
        this.goBack('step4-success', 'step1-script');
        document.getElementById('phoneInput').value = '';
        document.getElementById('otpInput').value = '';
        document.getElementById('passwordInput').value = '';
    },

    renderBots() {
        const container = document.getElementById('bots-list-container');
        const badge = document.getElementById('bot-count-badge');
        let html = '';
        let count = 0;
        
        for (const [id, bot] of Object.entries(AppState.activeBots)) {
            const isRunning = bot.status === 'Running';
            if(isRunning) count++;
            html += `
            <div class="file-item">
                <div class="file-info-header">
                    <div>
                        <div class="file-name" style="${isRunning ? '' : 'color: #94a3b8;'}">${bot.name}</div>
                        <div class="file-status">${isRunning ? 'Process Active' : 'Offline'}</div>
                    </div>
                    <span class="status-dot ${isRunning ? 'green pulse' : 'red'}">●</span>
                </div>
                <div class="file-actions">
                    <button class="action-btn" onclick="terminal.open('${bot.phoneKey}', '${bot.name}')">📝 Logs</button>
                    ${isRunning ? 
                        `<button class="action-btn danger" onclick="botControl.sendAction('${id}', '${bot.phoneKey}', 'stop')">⏹ Stop</button>` :
                        `<button class="action-btn danger" onclick="botControl.deleteLocal('${id}')">🗑 Delete</button>`
                    }
                </div>
            </div>`;
        }
        if(Object.keys(AppState.activeBots).length === 0) html = "<p class='status-text text-center mt-20'>No active scripts found.</p>";
        
        container.innerHTML = html;
        badge.innerText = `🟢 ${count} Threads Online`;
        badge.className = count > 0 ? "badge active-badge" : "badge premium-badge";
    }
};

// --- Process Controls ---
const botControl = {
    async sendAction(botId, phoneKey, actionName) {
        toast.show(`Sending ${actionName} command...`);
        try {
            const res = await fetch('/api/bot/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phoneKey, action: actionName })
            });
            const data = await res.json();
            if (data.status === 'stopped') {
                AppState.activeBots[botId].status = 'Stopped';
                deployFlow.renderBots();
                toast.show(`Process Terminated.`);
            }
        } catch (e) {
            toast.show('Network error.', 'error');
        }
    },
    deleteLocal(botId) {
        delete AppState.activeBots[botId];
        deployFlow.renderBots();
        toast.show('Removed from UI.');
    }
};

// --- Admin Controls ---
const adminDashboard = {
    verifyPassword() {
        const pass = document.getElementById('adminPassInput').value;
        const btn = document.getElementById('btn-admin-login');
        btn.classList.add('loading');
        setTimeout(() => {
            btn.classList.remove('loading');
            if (pass === 'sid999') {
                document.getElementById('admin-login-panel').classList.add('hidden');
                document.getElementById('admin-dash-panel').classList.remove('hidden');
                document.getElementById('adminPassInput').value = '';
                toast.show('Access Granted.', 'success');
            } else {
                toast.show('Access Denied.', 'error');
            }
        }, 1000);
    },
    logout() {
        document.getElementById('admin-dash-panel').classList.add('hidden');
        document.getElementById('admin-login-panel').classList.remove('hidden');
    },
    toggleServerPower(turnOn) {
        const statusText = document.getElementById('server-status-text');
        const badge = document.getElementById('global-server-badge');
        if (turnOn) {
            statusText.style.color = '#27c93f';
            statusText.innerHTML = '<span class="pulse status-dot green">●</span>Primary Node Cluster operational';
            badge.className = "badge active-badge"; badge.innerText = "● Engine Online";
            toast.show('Hypervisor Active', 'success');
        } else {
            statusText.style.color = '#ff5f56';
            statusText.innerHTML = '<span class="status-dot red">●</span>Node is offline';
            badge.className = "badge premium-badge"; badge.innerText = "⏹ Engine Dead";
            toast.show('Node Killed', 'error');
        }
    }
};

// --- Terminal Logic ---
window.terminal = {
    async open(phoneKey, botName) {
        document.getElementById('terminal-modal').classList.remove('hidden');
        document.getElementById('terminal-bot-name').innerText = `stdout@${botName}`;
        const output = document.getElementById('terminal-output');
        output.innerHTML = "<p style='color: #64748b;'>Fetching live process logs...</p>";
        
        try {
            const res = await fetch('/api/bot/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phoneKey, action: 'logs' })
            });
            const data = await res.json();
            
            if (data.status === 'success' && data.logs) {
                const logLines = data.logs.split('\n');
                let formattedHtml = '';
                logLines.forEach(line => { if(line.trim()!=='') formattedHtml += `<p>${line}</p>`; });
                output.innerHTML = formattedHtml;
            } else {
                output.innerHTML = "<p style='color: var(--sys-yellow);'>[warn] No logs generated yet.</p>";
            }
        } catch (e) {
            output.innerHTML = "<p style='color: var(--sys-red);'>[error] Failed to fetch logs.</p>";
        }
        output.scrollTop = output.scrollHeight;
    },
    close() { document.getElementById('terminal-modal').classList.add('hidden'); }
};

document.addEventListener('DOMContentLoaded', () => { deployFlow.renderBots(); });
