#!/usr/bin/env python3
"""
Mobile Web App for VFS Global Guinea-Bissau Booking
Runs on your phone's browser with responsive design
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
import base64
import io
from PIL import Image

# Prepare import path so we can import `app.services.*`
import sys
from pathlib import Path as _PathForSys
_ROOT_DIR = str(_PathForSys(__file__).resolve().parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

# Handle imports with fallback for different environments
# Import automation worker (do not null out everything if csv_io fails)
VFSBotWorker = None
AvailabilityStatus = None
BookingResult = None
ClientRecord = None
load_clients = None
save_clients = None

try:
    from app.services.vfs_automation import VFSBotWorker as _VFSBotWorker, AvailabilityStatus as _AvailabilityStatus, BookingResult as _BookingResult
    VFSBotWorker, AvailabilityStatus, BookingResult = _VFSBotWorker, _AvailabilityStatus, _BookingResult
except Exception as _e1:
    print(f"Warning: failed to import app.services.vfs_automation: {_e1}")
    try:
        from services.vfs_automation import VFSBotWorker as _VFSBotWorker, AvailabilityStatus as _AvailabilityStatus, BookingResult as _BookingResult
        VFSBotWorker, AvailabilityStatus, BookingResult = _VFSBotWorker, _AvailabilityStatus, _BookingResult
    except Exception as _e2:
        print(f"Warning: Automation worker not available. Ensure you run inside the project's virtual environment. Details: {_e2}")

# Import CSV utilities separately so a failure here does not break the worker
try:
    from app.services.csv_io import ClientRecord as _ClientRecord, load_clients as _load_clients, save_clients as _save_clients
    ClientRecord, load_clients, save_clients = _ClientRecord, _load_clients, _save_clients
except Exception:
    try:
        from services.csv_io import ClientRecord as _ClientRecord, load_clients as _load_clients, save_clients as _save_clients
        ClientRecord, load_clients, save_clients = _ClientRecord, _load_clients, _save_clients
    except Exception:
        print("Warning: CSV utilities not available. Client list features will be limited.")

app = Flask(__name__)
app.secret_key = 'vfs_booking_mobile_app_2024'

# Global variables for bot status
bot_status = {
    'running': False,
    'status': 'idle',
    'message': 'Ready to start',
    'availability': None,
    'bookings': [],
    'progress': {'current': 0, 'total': 0}
}

bot_worker = None

@app.route('/')
def index():
    """Main mobile interface with fallback template if missing."""
    tpl_path = Path('templates') / 'mobile_index.html'
    if tpl_path.exists():
        return render_template('mobile_index.html')
    # Enhanced mobile-optimized fallback UI
    return (
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
          <title>Guinea-Bissau Visa Booking</title>
          <style>
            * { box-sizing: border-box; }
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
              margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: #333; line-height: 1.5; min-height: 100vh;
            }
            .container { padding: 20px; max-width: 480px; margin: 0 auto; min-height: 100vh; }
            .card {
              background: rgba(255,255,255,0.95); backdrop-filter: blur(10px);
              border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);
              padding: 24px; margin-bottom: 20px;
            }
            h1 { font-size: 24px; font-weight: 700; margin: 0 0 8px; color: #2d3748; }
            .subtitle { font-size: 14px; color: #718096; margin-bottom: 24px; }
            .status-pill {
              display: inline-block; padding: 8px 16px; border-radius: 20px;
              font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
              margin-left: 12px;
            }
            .status-idle { background: #e2e8f0; color: #4a5568; }
            .status-running { background: #c6f6d5; color: #22543d; }
            .status-error { background: #fed7d7; color: #742a2a; }
            .status-starting { background: #bee3f8; color: #2a4365; }
            .status-stopped { background: #faf089; color: #744210; }
            
            .form-group { margin-bottom: 20px; }
            label { display: block; font-size: 16px; font-weight: 600; margin-bottom: 8px; color: #2d3748; }
            input[type="text"] {
              width: 100%; padding: 16px; border: 2px solid #e2e8f0; border-radius: 12px;
              font-size: 16px; background: #fff; transition: border-color 0.2s;
            }
            input[type="text"]:focus { outline: none; border-color: #667eea; }
            input[type="text"]::placeholder { color: #a0aec0; }
            
            .checkbox-group { display: flex; gap: 20px; margin: 20px 0; }
            .checkbox-item {
              display: flex; align-items: center; gap: 8px;
              font-size: 16px; font-weight: 500; color: #4a5568;
            }
            input[type="checkbox"] {
              width: 20px; height: 20px; accent-color: #667eea;
            }
            
            .button-group { display: flex; gap: 12px; margin: 24px 0; }
            button {
              flex: 1; padding: 16px 24px; border: none; border-radius: 12px;
              font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.2s;
              min-height: 56px;
            }
            .btn-primary {
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6); }
            .btn-primary:active { transform: translateY(0); }
            .btn-secondary {
              background: #f7fafc; color: #4a5568; border: 2px solid #e2e8f0;
            }
            .btn-secondary:hover { background: #edf2f7; border-color: #cbd5e0; }
            
            .status-area {
              margin-top: 20px; padding: 16px; background: #f7fafc;
              border-radius: 12px; border-left: 4px solid #667eea;
              min-height: 60px; display: flex; align-items: center;
            }
            .status-text { font-size: 16px; color: #4a5568; }
            .status-success { border-left-color: #48bb78; background: #f0fff4; }
            .status-error { border-left-color: #f56565; background: #fff5f5; }
            .status-info { border-left-color: #4299e1; background: #ebf8ff; }
            
            .notification {
              position: fixed; top: 20px; left: 20px; right: 20px;
              padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 600;
              z-index: 1000; transform: translateY(-100px); transition: transform 0.3s ease;
            }
            .notification.show { transform: translateY(0); }
            .notification-success { background: #c6f6d5; color: #22543d; }
            .notification-error { background: #fed7d7; color: #742a2a; }
            .notification-info { background: #bee3f8; color: #2a4365; }
            
            @media (max-width: 480px) {
              .container { padding: 16px; }
              .card { padding: 20px; }
              h1 { font-size: 22px; }
              .checkbox-group { flex-direction: column; gap: 12px; }
              .button-group { flex-direction: column; }
            }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="card">
              <h1>Guinea-Bissau Visa Booking <span class="status-pill status-idle" id="pill">idle</span></h1>
              <div class="subtitle">Automated appointment booking system</div>
              
              <div class="form-group">
                <label for="url">Start URL (optional)</label>
                <input id="url" type="text" placeholder="https://visa.vfsglobal.com/gnb/pt/prt/login" />
              </div>
              
              <div class="checkbox-group">
                <div class="checkbox-item">
                  <input id="headless" type="checkbox" checked />
                  <label for="headless">Headless Mode</label>
                </div>
                <div class="checkbox-item">
                  <input id="playwright" type="checkbox" checked />
                  <label for="playwright">Use Playwright</label>
                </div>
              </div>
              
              <div class="button-group">
                <button id="start" class="btn-primary">Start Bot</button>
                <button id="stop" class="btn-secondary">Stop Bot</button>
              </div>
              
              <div class="status-area" id="statusArea">
                <div class="status-text" id="status">Ready to start automation</div>
              </div>
            </div>
          </div>
          
          <div id="notification" class="notification"></div>
          
          <script>
            const statusEl = document.getElementById('status');
            const statusArea = document.getElementById('statusArea');
            const pill = document.getElementById('pill');
            const notification = document.getElementById('notification');
            
            function setStatus(text, type = 'info') {
              statusEl.textContent = text || 'Ready to start automation';
              statusArea.className = `status-area status-${type}`;
            }
            
            function setPill(status) {
              pill.textContent = status;
              pill.className = `status-pill status-${status}`;
            }
            
            function showNotification(message, type = 'info') {
              notification.textContent = message;
              notification.className = `notification notification-${type}`;
              notification.classList.add('show');
              setTimeout(() => notification.classList.remove('show'), 3000);
            }
            
            async function call(path, body) {
              const r = await fetch(path, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body || {})
              });
              const j = await r.json();
              if (!r.ok) throw new Error(j.error || ('HTTP ' + r.status));
              return j;
            }
            
            document.getElementById('start').onclick = async () => {
              try {
                setPill('starting');
                setStatus('Initializing bot...', 'info');
                showNotification('Starting automation...', 'info');
                
                const payload = {
                  headless: document.getElementById('headless').checked,
                  use_playwright: document.getElementById('playwright').checked,
                  monitoring_duration: 4,
                  start_url: (document.getElementById('url').value || '').trim()
                };
                
                const res = await call('/api/start_bot', payload);
                setPill('running');
                setStatus(res.message || 'Bot is running and monitoring...', 'success');
                showNotification('Bot started successfully!', 'success');
              } catch (e) {
                setPill('error');
                setStatus('Error: ' + e.message, 'error');
                showNotification('Failed to start bot: ' + e.message, 'error');
              }
            };
            
            document.getElementById('stop').onclick = async () => {
              try {
                const res = await call('/api/stop_bot', {});
                setPill('stopped');
                setStatus(res.message || 'Bot stopped', 'info');
                showNotification('Bot stopped successfully', 'info');
              } catch (e) {
                setPill('error');
                setStatus('Error: ' + e.message, 'error');
                showNotification('Failed to stop bot: ' + e.message, 'error');
              }
            };
            
            // Auto-refresh status every 5 seconds when running
            setInterval(async () => {
              if (pill.textContent === 'running') {
                try {
                  const res = await fetch('/api/status');
                  const data = await res.json();
                  if (data.status) {
                    setStatus(data.message || 'Bot is running...', 'success');
                  }
                } catch (e) {
                  // Silent fail for status updates
                }
              }
            }, 5000);
          </script>
        </body>
        </html>
        """,
        200,
        {"Content-Type": "text/html; charset=utf-8"}
    )

@app.route('/api/ping')
def ping():
    return jsonify({"ok": True, "message": "mobile app alive"})

@app.route('/api/status')
def get_status():
    """Get current bot status."""
    return jsonify(bot_status)

@app.route('/api/clients')
def get_clients():
    """Get all clients from CSV."""
    try:
        clients = load_clients('clients.csv')
        return jsonify([{
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email,
            'mobile_number': c.mobile_number,
            'passport_number': c.passport_number
        } for c in clients])
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_client', methods=['POST'])
def save_client():
    """Save client data."""
    try:
        data = request.json
        client = ClientRecord(
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=data['date_of_birth'],
            email=data['email'],
            password=data['password'],
            mobile_country_code=data['mobile_country_code'],
            mobile_number=data['mobile_number'],
            passport_number=data.get('passport_number', ''),
            visa_type=(data.get('visa_type') or data.get('trip_reason') or '').strip(),
            application_center=data.get('application_center', ''),
            service_center=data.get('service_center', ''),
            trip_reason=data.get('trip_reason', ''),
            gender=data.get('gender', ''),
            current_nationality=data.get('current_nationality', ''),
            passport_expiry=data.get('passport_expiry', '')
        )
        
        # Load existing clients
        try:
            existing_clients = load_clients('clients.csv')
        except FileNotFoundError:
            existing_clients = []
        
        # Check for duplicate email
        for existing in existing_clients:
            if existing.email == client.email:
                return jsonify({'error': 'Email already exists'}), 400
        
        # Add new client
        existing_clients.append(client)
        # Correct argument order: path first, then clients
        save_clients('clients.csv', existing_clients)
        
        return jsonify({'success': True, 'message': 'Client saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """Start the VFS automation bot."""
    global bot_worker, bot_status
    
    if bot_status['running']:
        return jsonify({'error': 'Bot is already running'}), 400
    
    try:
        # Defensive guard: worker not available (e.g., ran outside venv)
        if VFSBotWorker is None:
            raise RuntimeError('Automation worker unavailable. Please run: pip install -r requirements.txt && python -m playwright install')
        
        data = request.json
        headless = data.get('headless', True)
        use_playwright = data.get('use_playwright', True)
        monitoring_duration = data.get('monitoring_duration', 4)
        start_url = (data.get('start_url') or '').strip()
        
        # Update status
        bot_status['running'] = True
        bot_status['status'] = 'starting'
        bot_status['message'] = 'Initializing bot...'
        
        # Start bot worker in background thread
        try:
            bot_worker = VFSBotWorker(headless=headless, use_playwright=use_playwright, start_url=start_url or None)
            bot_worker.monitoring_duration = monitoring_duration
        except Exception as e:
            # Check for specific dependency issues
            error_msg = str(e).lower()
            if 'playwright' in error_msg:
                raise RuntimeError('Playwright not installed. Run: pip install playwright && python -m playwright install')
            elif 'selenium' in error_msg:
                raise RuntimeError('Selenium not installed. Run: pip install selenium')
            elif 'pyqt' in error_msg:
                raise RuntimeError('PyQt6 not installed. Run: pip install PyQt6')
            else:
                raise RuntimeError(f'Bot initialization failed: {str(e)}')
        
        # Connect signals
        try:
            bot_worker.status_updated.connect(lambda msg: update_bot_status('status', msg))
            bot_worker.availability_found.connect(lambda status: update_bot_status('availability', status))
            bot_worker.booking_completed.connect(lambda result: update_bot_status('booking', result))
            bot_worker.error_occurred.connect(lambda error: update_bot_status('error', error))
            bot_worker.progress_updated.connect(lambda current, total: update_bot_status('progress', {'current': current, 'total': total}))
        except AttributeError:
            # Fallback worker (without PyQt signals) exposes callables directly
            bot_worker.status_updated = lambda msg: update_bot_status('status', msg)
            bot_worker.availability_found = lambda status: update_bot_status('availability', status)
            bot_worker.booking_completed = lambda result: update_bot_status('booking', result)
            bot_worker.error_occurred = lambda error: update_bot_status('error', error)
            bot_worker.progress_updated = lambda current, total: update_bot_status('progress', {'current': current, 'total': total})
        
        # Start worker
        # If it's a QThread worker, use start(); otherwise run in a Python thread
        if hasattr(bot_worker, 'start'):
            bot_worker.start()
        else:
            threading.Thread(target=bot_worker.run, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Bot started successfully'})
    except Exception as e:
        bot_status['running'] = False
        bot_status['status'] = 'error'
        bot_status['message'] = f'Failed to start bot: {str(e)}'
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the VFS automation bot."""
    global bot_worker, bot_status
    
    if not bot_status['running']:
        return jsonify({'error': 'Bot is not running'}), 400
    
    try:
        if bot_worker:
            # Try to stop the worker gracefully
            try:
                if hasattr(bot_worker, 'stop'):
                    bot_worker.stop()
                elif hasattr(bot_worker, 'request_stop'):
                    bot_worker.request_stop()
                
                # Wait for worker to finish
                if hasattr(bot_worker, 'wait'):
                    bot_worker.wait(3000)  # Wait up to 3 seconds
                elif hasattr(bot_worker, 'join'):
                    bot_worker.join(timeout=3)
                    
            except Exception as stop_error:
                print(f"Warning: Error stopping worker: {stop_error}")
                # Continue with cleanup even if stop fails
        
        # Reset status
        bot_status['running'] = False
        bot_status['status'] = 'stopped'
        bot_status['message'] = 'Bot stopped successfully'
        bot_status['availability'] = None
        bot_status['bookings'] = []
        bot_status['progress'] = {'current': 0, 'total': 0}
        
        # Clear worker reference
        bot_worker = None
        
        return jsonify({'success': True, 'message': 'Bot stopped successfully'})
    except Exception as e:
        # Force reset status even if there's an error
        bot_status['running'] = False
        bot_status['status'] = 'error'
        bot_status['message'] = f'Error stopping bot: {str(e)}'
        bot_worker = None
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    """Handle image upload for passport photos."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Create info directory
        info_dir = Path('info')
        info_dir.mkdir(exist_ok=True)
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"passport_photo_{timestamp}.jpg"
        filepath = info_dir / filename
        
        # Convert to PIL Image and save
        image = Image.open(file.stream)
        image.save(filepath, 'JPEG', quality=95)
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'filename': filename,
            'path': str(filepath)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_bot_status(status_type, data):
    """Update bot status from worker thread."""
    global bot_status
    
    if status_type == 'status':
        bot_status['message'] = data
    elif status_type == 'availability':
        bot_status['availability'] = {
            'available': data.available,
            'slots_count': data.slots_count,
            'last_checked': data.last_checked,
            'error_message': data.error_message
        }
        bot_status['message'] = f"Availability found: {data.slots_count} slots" if data.available else "No availability found"
    elif status_type == 'booking':
        bot_status['bookings'].append({
            'success': data.success,
            'client_email': data.client_email,
            'booking_reference': data.booking_reference,
            'error_message': data.error_message,
            'timestamp': data.timestamp
        })
        bot_status['message'] = f"Booking {'successful' if data.success else 'failed'} for {data.client_email}"
    elif status_type == 'error':
        bot_status['status'] = 'error'
        bot_status['message'] = f"Error: {data}"
    elif status_type == 'progress':
        bot_status['progress'] = data

if __name__ == '__main__':
    # Create templates directory
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Create static directory
    static_dir = Path('static')
    static_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting VFS Global Mobile App...")
    print("📱 Open your phone's browser and go to:")
    print("   http://YOUR_COMPUTER_IP:5000")
    print("   (Replace YOUR_COMPUTER_IP with your computer's IP address)")
    print("\n💡 To find your IP address:")
    print("   Windows: ipconfig")
    print("   Mac/Linux: ifconfig")
    
    # Run on all interfaces (0.0.0.0) so phone can access it
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
