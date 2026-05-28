# -*- coding: utf-8 -*-
import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
from flask import Flask, send_file, redirect, request, jsonify
from werkzeug.utils import secure_filename
from threading import Thread

# --- Configuration ---
TOKEN = '6067177575:AAEip8P4fVsQDEpG_LiNRTyqKFiPgy04qvs' 
OWNER_ID = 2119464081
ADMIN_ID = 2119464081
YOUR_USERNAME = '@Xricx0' 
UPDATE_CHANNEL = 'https://t.me/+5uCnxp3U1gMwZjQ1'

# ⚠️ IMPORTANT: Change this to your actual server/hosting URL!
HOSTING_DOMAIN = "https://your-server-url.com" 

# Folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')
MENU_VIDEO_PATH = os.path.join(BASE_DIR, 'menu_video.mp4')

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

# Initialize bot & Data Structures
bot = telebot.TeleBot(TOKEN)
bot_scripts = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}

# --- Backend Flask API & Pro Web App ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Hosting Server Running Securely."

@app.route('/menu_video.mp4')
def serve_video():
    if os.path.exists(MENU_VIDEO_PATH): return send_file(MENU_VIDEO_PATH, mimetype='video/mp4')
    return redirect("https://www.w3schools.com/html/mov_bbb.mp4")

@app.route('/webapp')
def webapp():
    """The Highly Attractive Pro Web App UI with Userbot Logic"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --bg: #0f172a; --panel: rgba(30, 41, 59, 0.7); --primary: #3b82f6; --glow: rgba(59, 130, 246, 0.5);
                --text: #f8fafc; --muted: #94a3b8; --success: #10b981;
            }
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background-color: var(--bg); color: var(--text);
                margin: 0; padding: 20px; text-align: center; overflow-x: hidden;
            }
            .glass-panel {
                background: var(--panel); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
                padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }
            h2 { margin-top: 0; font-size: 24px; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; color: transparent; }
            p { color: var(--muted); font-size: 14px; margin-bottom: 20px; }
            
            /* Inputs & Buttons */
            input[type="file"], input[type="text"], input[type="password"] {
                width: 100%; padding: 15px; margin: 10px 0; border-radius: 12px;
                background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2);
                color: white; font-size: 16px; box-sizing: border-box; outline: none; transition: 0.3s;
            }
            input:focus { border-color: var(--primary); box-shadow: 0 0 15px var(--glow); }
            
            .btn {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white;
                border: none; padding: 15px 25px; border-radius: 12px; font-size: 16px; font-weight: bold;
                cursor: pointer; width: 100%; margin-top: 10px; transition: all 0.3s ease;
                box-shadow: 0 4px 15px var(--glow);
            }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6); }
            .btn:active { transform: translateY(1px); }
            
            /* Step Wizard Animation */
            .step { display: none; animation: fadeIn 0.4s ease forwards; }
            .step.active { display: block; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            
            /* Status Loader */
            .loader { display: none; margin: 20px auto; border: 4px solid rgba(255,255,255,0.1); border-top: 4px solid var(--primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>

        <div class="glass-panel">
            <h2><i class="fa-solid fa-robot"></i> Userbot Hub</h2>
            <p>Deploy and authenticate your script seamlessly.</p>
        </div>

        <div class="glass-panel">
            <div id="step-upload" class="step active">
                <h3><i class="fa-solid fa-file-code"></i> Setup Script</h3>
                <input type="text" id="apiId" placeholder="API ID (e.g. 123456)" />
                <input type="password" id="apiHash" placeholder="API HASH" />
                <input type="file" id="scriptFile" accept=".py,.zip" />
                <button class="btn" onclick="deployScript()"><i class="fa-solid fa-rocket"></i> Deploy & Start</button>
            </div>

            <div id="step-phone" class="step">
                <h3><i class="fa-solid fa-phone"></i> Terminal Authentication</h3>
                <p>Script is running. Enter the phone number to login.</p>
                <input type="text" id="phoneInput" placeholder="+1234567890" />
                <button class="btn" onclick="sendTerminalInput('phone')">Submit Number</button>
            </div>

            <div id="step-otp" class="step">
                <h3><i class="fa-solid fa-key"></i> OTP Code</h3>
                <p>Check Telegram for your login code.</p>
                <input type="text" id="otpInput" placeholder="12345" />
                <button class="btn" onclick="sendTerminalInput('otp')">Submit OTP</button>
            </div>

            <div id="step-pass" class="step">
                <h3><i class="fa-solid fa-lock"></i> 2FA Password</h3>
                <p>Enter your Two-Step Verification password (if any).</p>
                <input type="password" id="passInput" placeholder="Password (leave blank if none)" />
                <button class="btn" onclick="sendTerminalInput('pass')">Complete Login</button>
            </div>
            
            <div id="step-success" class="step">
                <h3><i class="fa-solid fa-circle-check" style="color: var(--success);"></i> Userbot Online</h3>
                <p>Authentication complete. Your bot is now running in the background.</p>
                <button class="btn" onclick="Telegram.WebApp.close()">Close Dashboard</button>
            </div>
            
            <div id="loader" class="loader"></div>
            <p id="status-msg" style="margin-top:15px; color: #fbbf24;"></p>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            const userId = tg.initDataUnsafe?.user?.id || 1; 

            function showStep(stepId) {
                document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
                document.getElementById('step-' + stepId).classList.add('active');
            }

            function setStatus(msg, showLoader=false) {
                document.getElementById('status-msg').innerText = msg;
                document.getElementById('loader').style.display = showLoader ? 'block' : 'none';
            }

            async function deployScript() {
                const fileInput = document.getElementById('scriptFile');
                const apiId = document.getElementById('apiId').value;
                const apiHash = document.getElementById('apiHash').value;
                
                if (!fileInput.files[0]) return setStatus("⚠️ Please select a file first.");
                if (!apiId || !apiHash) return setStatus("⚠️ API ID and API HASH are required.");
                
                setStatus("Uploading & Starting script...", true);
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('user_id', userId);
                formData.append('api_id', apiId);
                formData.append('api_hash', apiHash);

                try {
                    const response = await fetch('/api/deploy', { method: 'POST', body: formData });
                    const result = await response.json();
                    if(result.success) {
                        setStatus("");
                        showStep('phone'); 
                    } else {
                        setStatus("❌ Error: " + result.error);
                    }
                } catch (e) {
                    setStatus("❌ Network error.");
                }
            }

            async function sendTerminalInput(step) {
                let valId = step === 'phone' ? 'phoneInput' : step === 'otp' ? 'otpInput' : 'passInput';
                let val = document.getElementById(valId).value;
                
                setStatus(`Sending ${step}...`, true);
                
                try {
                    const response = await fetch('/api/input', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ user_id: userId, step: step, input_data: val })
                    });
                    const result = await response.json();
                    
                    if(result.success) {
                        setStatus("");
                        if(step === 'phone') showStep('otp');
                        else if(step === 'otp') showStep('pass');
                        else showStep('success');
                    } else {
                        setStatus("❌ " + result.error);
                    }
                } catch (e) {
                    setStatus("❌ Failed to send data to terminal.");
                }
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    """Receives the script and API details, saves it, and starts it with injected env vars."""
    if 'file' not in request.files: return jsonify({"success": False, "error": "No file uploaded"})
    file = request.files['file']
    user_id = request.form.get('user_id')
    api_id = request.form.get('api_id', '')
    api_hash = request.form.get('api_hash', '')
    
    if not user_id: return jsonify({"success": False, "error": "User ID missing"})
    user_id = int(user_id)
    
    filename = secure_filename(file.filename)
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    
    file_path = os.path.join(user_folder, filename)
    file.save(file_path)
    
    # Inject API ID and API HASH into the script's environment
    custom_env = os.environ.copy()
    custom_env["API_ID"] = api_id
    custom_env["API_HASH"] = api_hash
    
    script_key = f"{user_id}_{filename}"
    try:
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(filename)[0]}.log")
        log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        
        # Start the process with the custom environment variables
        process = subprocess.Popen([sys.executable, file_path], cwd=user_folder, stdout=log_file, stderr=log_file, stdin=subprocess.PIPE, env=custom_env)
        
        bot_scripts[script_key] = {
            'process': process, 'log_file': log_file, 'file_name': filename,
            'script_owner_id': user_id, 'start_time': datetime.now()
        }
        return jsonify({"success": True, "message": "Script started"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/input', methods=['POST'])
def api_input():
    """Receives input and handles Pyrogram/Telethon specific terminal logic."""
    data = request.json
    user_id = int(data.get('user_id', 0))
    step = data.get('step', '')
    input_text = data.get('input_data', '')
    
    user_scripts = [script for key, script in bot_scripts.items() if script['script_owner_id'] == user_id]
    if not user_scripts:
        return jsonify({"success": False, "error": "No running script found for your account."})
        
    target_script = user_scripts[-1]
    process = target_script.get('process')
    
    if process and process.poll() is None:
        try:
            # 1. Write the main input (Phone, OTP, or Password)
            process.stdin.write((input_text + '\n').encode('utf-8'))
            process.stdin.flush()
            
            # 2. USERBOT LOGIC: Pyrogram asks "Is this phone correct? (y/N)" right after you enter a phone number.
            # We must simulate pressing 'y' and Enter automatically, otherwise the script hangs here forever.
            if step == 'phone':
                time.sleep(1) # Give Pyrogram 1 second to print the confirmation prompt
                process.stdin.write(('y\n').encode('utf-8')) 
                process.stdin.flush()
                
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": f"Terminal injection failed: {str(e)}"})
    return jsonify({"success": False, "error": "Script process crashed or stopped."})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- Standard Bot Handlers ---

def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    web_app_url = f"{HOSTING_DOMAIN}/webapp"
    
    b_webapp = types.InlineKeyboardButton('🚀 OPEN USERBOT DASHBOARD ✨', web_app=types.WebAppInfo(url=web_app_url))
    b_updates = types.InlineKeyboardButton('📢 Updates Channel', url=UPDATE_CHANNEL)
    b_contact = types.InlineKeyboardButton('📞 Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}')
    
    markup.add(b_webapp)
    markup.add(b_updates)
    markup.add(b_contact)
    return markup

@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message):
    user_id = message.from_user.id
    if user_id not in active_users: active_users.add(user_id)
    
    bot.send_message(
        message.chat.id, 
        "Welcome to the **Userbot Hosting Hub**. Click the button below to open the interactive deployment dashboard.", 
        parse_mode="Markdown",
        reply_markup=create_main_menu_inline(user_id)
    )

def cleanup():
    for key, script_info in bot_scripts.items():
        try:
            process = script_info.get('process')
            if process: process.kill()
            if 'log_file' in script_info and not script_info['log_file'].closed: script_info['log_file'].close()
        except: pass
atexit.register(cleanup)

if __name__ == '__main__':
    keep_alive()
    print("🚀 Bot and API Server Started")
    while True:
        try: bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e: time.sleep(15)

