#!/usr/bin/env python3
"""
SonicWave Web Transmitter Dashboard
A zero-dependency local web app for effortless ultrasonic text transmission.
"""

import os
import sys
import json
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure script dir and root are in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import numpy as np
import sounddevice as sd

from sonicwave.config import SonicConfig, ProfileType
from sonicwave.modulation import SonicModulator
from sonicwave.mixer import generate_ambient_music_sample, mix_music_and_data


class TransmitterEngine:
    def __init__(self, profile_type: ProfileType = ProfileType.UNIVERSAL_48K):
        self.config = SonicConfig.get_profile(profile_type)
        self.modulator = SonicModulator(self.config)
        self.history = ["Hello", "Jigar", "Hi this is jigar i can see you"]
        
        self.is_playing = False
        self.is_looping = False
        self.current_text = ""
        self.playback_thread = None
        self.stop_requested = False
        
        # Pre-synthesize ambient music for instant playback response
        self.ambient_music = generate_ambient_music_sample(duration_sec=14.0, sample_rate=self.config.sample_rate)
        try:
            self.device_name = sd.query_devices(kind='output')['name']
        except Exception:
            self.device_name = "Default Speakers"

    def stop(self):
        """Immediately stops any running audio transmission."""
        self.stop_requested = True
        self.is_looping = False
        try:
            sd.stop()
        except Exception:
            pass
        self.is_playing = False

    def transmit(self, text: str, loop: bool = False, delay_sec: float = 2.0):
        """Launches transmission in a background thread."""
        self.stop()
        time.sleep(0.05)
        self.stop_requested = False
        
        text = text.strip()
        if not text:
            return False, "Text cannot be empty"
            
        payload_bytes = text.encode('utf-8')
        if len(payload_bytes) > 255:
            return False, f"Text exceeds 255 bytes limit ({len(payload_bytes)} bytes)"
            
        if text not in self.history:
            self.history.insert(0, text)
            if len(self.history) > 25:
                self.history.pop()

        self.current_text = text
        self.is_looping = loop
        
        def run():
            self.is_playing = True
            try:
                # Modulate ultrasonic burst
                ultrasonic_audio = self.modulator.modulate_packet(payload_bytes)
                mixed_audio = mix_music_and_data(self.ambient_music, ultrasonic_audio, self.config, offset_sec=1.0)
                duration = len(mixed_audio) / self.config.sample_rate

                while not self.stop_requested:
                    sd.play(mixed_audio, self.config.sample_rate)
                    
                    # Sleep in small increments to be responsive to stop requests
                    elapsed = 0.0
                    while elapsed < duration and not self.stop_requested:
                        time.sleep(0.05)
                        elapsed += 0.05
                        
                    sd.wait()
                    
                    if not self.is_looping or self.stop_requested:
                        break
                        
                    # Delay between loops
                    delay_elapsed = 0.0
                    while delay_elapsed < delay_sec and not self.stop_requested:
                        time.sleep(0.05)
                        delay_elapsed += 0.05
                        
            except Exception as e:
                print(f"[!] Playback error: {e}")
            finally:
                self.is_playing = False
                self.is_looping = False

        self.playback_thread = threading.Thread(target=run, daemon=True)
        self.playback_thread.start()
        return True, "Transmission started"


engine = TransmitterEngine()


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SonicWave Transmitter Dashboard</title>
  <style>
    :root {
      --bg: #0c0f17;
      --card-bg: rgba(22, 27, 41, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #06b6d4;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --success: #10b981;
      --danger: #ef4444;
      --glow: rgba(59, 130, 246, 0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body {
      background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0c0f17 70%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px 16px;
    }
    .container {
      width: 100%;
      max-width: 680px;
    }
    header {
      text-align: center;
      margin-bottom: 28px;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 999px;
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #60a5fa;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 12px;
    }
    .badge-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #60a5fa;
      box-shadow: 0 0 8px #60a5fa;
    }
    h1 {
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 6px;
      background: linear-gradient(135deg, #ffffff 40%, #93c5fd 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p.subtitle {
      color: var(--text-muted);
      font-size: 14px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      backdrop-filter: blur(16px);
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }
    .form-group {
      margin-bottom: 18px;
    }
    label {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
    }
    textarea {
      width: 100%;
      height: 90px;
      padding: 14px 16px;
      background: rgba(12, 15, 23, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 12px;
      color: var(--text);
      font-size: 16px;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      transition: all 0.2s ease;
    }
    textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--glow);
    }
    .presets {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
    }
    .preset-pill {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #cbd5e1;
      font-size: 12px;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .preset-pill:hover {
      background: rgba(59, 130, 246, 0.2);
      border-color: rgba(59, 130, 246, 0.4);
      color: #fff;
      transform: translateY(-1px);
    }
    .controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 20px;
      padding: 12px 16px;
      background: rgba(12, 15, 23, 0.5);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .toggle-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      font-weight: 500;
    }
    .switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: rgba(255, 255, 255, 0.15);
      transition: .3s;
      border-radius: 24px;
    }
    .slider:before {
      position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
      background-color: white;
      transition: .3s;
      border-radius: 50%;
    }
    input:checked + .slider { background-color: var(--primary); }
    input:checked + .slider:before { transform: translateX(20px); }
    .btn-group {
      display: flex;
      gap: 12px;
    }
    button.btn-primary {
      flex: 1;
      padding: 14px 24px;
      background: linear-gradient(135deg, var(--primary) 0%, #1d4ed8 100%);
      color: white;
      border: none;
      border-radius: 12px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 15px var(--glow);
      transition: all 0.2s ease;
    }
    button.btn-primary:hover {
      background: linear-gradient(135deg, #60a5fa 0%, var(--primary) 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
    }
    button.btn-primary:active { transform: translateY(1px); }
    button.btn-danger {
      padding: 14px 20px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #f87171;
      border-radius: 12px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    button.btn-danger:hover {
      background: rgba(239, 68, 68, 0.3);
      color: #fff;
    }
    .status-panel {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      background: rgba(12, 15, 23, 0.6);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      margin-top: 16px;
    }
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
    }
    .status-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #64748b;
    }
    .status-dot.active {
      background: var(--success);
      box-shadow: 0 0 10px var(--success);
      animation: pulse 1.2s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.2); opacity: 1; }
      100% { transform: scale(0.95); opacity: 0.8; }
    }
    .device-info {
      font-size: 12px;
      color: var(--text-muted);
    }
    .history-card {
      margin-top: 20px;
    }
    .history-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 12px;
    }
    .history-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .history-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: rgba(12, 15, 23, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.04);
      border-radius: 10px;
      font-size: 14px;
    }
    .history-item button {
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #93c5fd;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.15s;
    }
    .history-item button:hover {
      background: var(--primary);
      color: white;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge"><div class="badge-dot"></div> Ultrasonic Transmitter (19.2 kHz)</div>
      <h1>SonicWave Studio</h1>
      <p class="subtitle">Broadcast text silently into room air through MacBook Pro speakers</p>
    </header>

    <div class="card">
      <div class="form-group">
        <label>
          <span>Payload Message</span>
          <span id="charCount">0 bytes / 255</span>
        </label>
        <textarea id="messageInput" placeholder="Type text here to transmit to iPhone... (e.g. 'Hello world')">Hello</textarea>
      </div>

      <div class="presets">
        <span class="preset-pill" onclick="setPreset('Hello')">👋 Hello</span>
        <span class="preset-pill" onclick="setPreset('Jigar')">👤 Jigar</span>
        <span class="preset-pill" onclick="setPreset('Hi this is jigar i can see you')">💬 Full Sentence</span>
        <span class="preset-pill" onclick="setPreset('Hello world')">🌍 Hello world</span>
        <span class="preset-pill" onclick="setPreset('SonicWave 🌊')">🌊 SonicWave</span>
      </div>

      <div class="controls">
        <div class="toggle-wrap">
          <label class="switch">
            <input type="checkbox" id="loopToggle">
            <span class="slider"></span>
          </label>
          <span>Loop Continuously</span>
        </div>
        <div style="font-size: 12px; color: var(--text-muted);">
          Shortcut: <kbd style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">⌘ + Enter</kbd>
        </div>
      </div>

      <div class="btn-group">
        <button class="btn-primary" id="transmitBtn" onclick="transmit()">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          Transmit Now
        </button>
        <button class="btn-danger" id="stopBtn" onclick="stopTransmission()">Stop</button>
      </div>

      <div class="status-panel">
        <div class="status-indicator">
          <div class="status-dot" id="statusDot"></div>
          <span id="statusText">Idle (Ready)</span>
        </div>
        <div class="device-info" id="deviceInfo">MacBook Pro Speakers</div>
      </div>
    </div>

    <div class="card history-card">
      <div class="history-title">Recent Transmissions</div>
      <div class="history-list" id="historyList"></div>
    </div>
  </div>

  <script>
    const input = document.getElementById('messageInput');
    const charCount = document.getElementById('charCount');
    const loopToggle = document.getElementById('loopToggle');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const deviceInfo = document.getElementById('deviceInfo');
    const historyList = document.getElementById('historyList');

    function updateByteCount() {
      const bytes = new TextEncoder().encode(input.value).length;
      charCount.textContent = `${bytes} bytes / 255`;
      charCount.style.color = bytes > 255 ? '#ef4444' : '#94a3b8';
    }
    input.addEventListener('input', updateByteCount);
    updateByteCount();

    function setPreset(txt) {
      input.value = txt;
      updateByteCount();
      input.focus();
    }

    input.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        transmit();
      }
    });

    async function transmit(customText) {
      const text = customText || input.value;
      if (!text.trim()) return;
      
      statusText.textContent = `Transmitting "${text}"...`;
      statusDot.className = 'status-dot active';

      try {
        const res = await fetch('/api/transmit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text,
            loop: loopToggle.checked,
            delay: 2.0
          })
        });
        const data = await res.json();
        pollStatus();
      } catch (err) {
        statusText.textContent = 'Network Error';
      }
    }

    async function stopTransmission() {
      await fetch('/api/stop', { method: 'POST' });
      pollStatus();
    }

    async function pollStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        deviceInfo.textContent = `${data.device} | ${data.carrier_freq} Hz`;

        if (data.is_playing) {
          statusDot.className = 'status-dot active';
          statusText.textContent = data.is_looping 
            ? `Looping "${data.current_text}"` 
            : `Transmitting "${data.current_text}"`;
        } else {
          statusDot.className = 'status-dot';
          statusText.textContent = 'Idle (Ready)';
        }

        renderHistory(data.history);
      } catch (e) {}
    }

    function renderHistory(items) {
      if (!items) return;
      historyList.innerHTML = items.map(item => `
        <div class="history-item">
          <span>"${escapeHtml(item)}"</span>
          <button onclick="transmit('${escapeHtml(item).replace(/'/g, "\\'")}')">Transmit</button>
        </div>
      `).join('');
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    setInterval(pollStatus, 800);
    pollStatus();
  </script>
</body>
</html>
"""


class WebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logging

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            status_data = {
                "is_playing": engine.is_playing,
                "is_looping": engine.is_looping,
                "current_text": engine.current_text,
                "carrier_freq": engine.config.carrier_freq,
                "sample_rate": engine.config.sample_rate,
                "device": engine.device_name,
                "history": engine.history,
            }
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/transmit':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            text = data.get('text', '')
            loop = bool(data.get('loop', False))
            delay = float(data.get('delay', 2.0))
            
            success, msg = engine.transmit(text, loop=loop, delay_sec=delay)
            self.send_response(200 if success else 400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "message": msg}).encode('utf-8'))
            
        elif self.path == '/api/stop':
            engine.stop()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def start_server(port: int = 5005, open_browser: bool = True):
    HTTPServer.allow_reuse_address = True
    server = None
    target_port = port
    
    # Try port 5005, then 5006, 5007 if busy
    for p in range(target_port, target_port + 5):
        try:
            server = HTTPServer(('0.0.0.0', p), WebHandler)
            target_port = p
            break
        except OSError:
            continue
            
    if server is None:
        print(f"[!] Error: Could not bind to any port in range {port}-{port+4}")
        sys.exit(1)
        
    url = f"http://127.0.0.1:{target_port}"
    print("=" * 65)
    print("           SONICWAVE WEB TRANSMITTER DASHBOARD")
    print("=" * 65)
    print(f"[*] Server listening on: {url}")
    print(f"[*] Local network access: http://localhost:{target_port}")
    print(f"[*] Audio Device       : {engine.device_name}")
    print(f"[*] Ultrasonic Carrier : {engine.config.carrier_freq:.0f} Hz (silent)")
    print("=" * 65)
    print("Dashboard is live! Opening browser... (Press Ctrl+C to stop)")
    
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        engine.stop()
        server.server_close()
        print("Server stopped.")


if __name__ == '__main__':
    port = 5005
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(port=port)
