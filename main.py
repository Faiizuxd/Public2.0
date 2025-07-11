from flask import Flask, request, render_template_string, redirect, session
import threading
import requests
import time
import os
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "faizu_secret_key"
ADMIN_PASSWORD = "12341234"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('bot_manager.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            thread_key TEXT PRIMARY KEY,
            thread_id TEXT,
            token TEXT,
            prefix TEXT,
            bot_name TEXT,
            start_time TEXT,
            status TEXT,
            message_count INTEGER,
            last_message TEXT,
            session_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
active_threads = {}

def get_db():
    conn = sqlite3.connect('bot_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def message_sender(token, thread_id, prefix, delay, messages, thread_key, bot_name, session_id):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'referer': 'https://www.facebook.com/',
        'Origin': 'https://www.facebook.com'
    }

    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO bots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
        thread_key, thread_id, token, prefix, bot_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'running', 0, '', session_id
    ))
    conn.commit()
    conn.close()

    while active_threads.get(thread_key, False):
        for msg in messages:
            if not active_threads.get(thread_key, False):
                break
            try:
                full_message = f"{prefix} {msg}"
                url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                payload = {
                    'access_token': token,
                    'message': full_message,
                    'client': 'mercury'
                }
                requests.post(url, data=payload, headers=headers, timeout=30)

                conn = get_db()
                conn.execute('UPDATE bots SET message_count = message_count + 1, last_message = ? WHERE thread_key = ?',
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), thread_key))
                conn.commit()
                conn.close()

                time.sleep(delay)
            except:
                time.sleep(30)

    conn = get_db()
    conn.execute('UPDATE bots SET status = "stopped" WHERE thread_key = ?', (thread_key,))
    conn.commit()
    conn.close()
    active_threads.pop(thread_key, None)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        mode = request.form.get('mode')
        thread_id = request.form.get('threadId')
        prefix = request.form.get('kidx')
        bot_name = request.form.get('botName') or 'My Bot'
        delay = max(1, int(request.form.get('time')))
        session_id = session.get('sid') or str(random.randint(100000, 999999))
        session['sid'] = session_id
        messages = [m.strip() for m in request.files['txtFile'].read().decode().splitlines() if m.strip()]

        if mode == 'single':
            token = request.form.get('accessToken').strip()
            thread_key = f"{thread_id}_{random.randint(1000, 9999)}"
            active_threads[thread_key] = True
            threading.Thread(target=message_sender, args=(token, thread_id, prefix, delay, messages, thread_key, bot_name, session_id), daemon=True).start()

        elif mode == 'multi':
            tokens = request.files['tokenFile'].read().decode().splitlines()
            for token in tokens:
                thread_key = f"{thread_id}_{random.randint(1000, 9999)}"
                active_threads[thread_key] = True
                threading.Thread(target=message_sender, args=(token.strip(), thread_id, prefix, delay, messages, thread_key, bot_name, session_id), daemon=True).start()

        return redirect('/status')

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SPAM BOT</title>
            <style>
                :root {
                    --dark: #121212;
                    --darker: #0a0a0a;
                    --darkest: #000000;
                    --light: #e0e0e0;
                    --accent: #6200ee;
                    --accent-hover: #3700b3;
                    --danger: #cf6679;
                }
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                }
                body {
                    background-color: var(--darkest);
                    color: var(--light);
                    min-height: 100vh;
                    padding: 2rem;
                    line-height: 1.6;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: var(--dark);
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                    padding: 2.5rem;
                    border: 1px solid rgba(255,255,255,0.05);
                }
                h2 {
                    color: var(--light);
                    text-align: center;
                    margin-bottom: 1.5rem;
                    font-size: 2rem;
                    font-weight: 600;
                    letter-spacing: -0.5px;
                }
                .form-group {
                    margin-bottom: 1.5rem;
                }
                label {
                    display: block;
                    margin-bottom: 0.5rem;
                    color: rgba(255,255,255,0.7);
                    font-size: 0.9rem;
                }
                input[type="text"], 
                input[type="number"],
                input[type="password"],
                input[type="file"] {
                    width: 100%;
                    padding: 0.8rem 1rem;
                    background: var(--darker);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 4px;
                    color: var(--light);
                    font-size: 1rem;
                    transition: all 0.3s ease;
                }
                input[type="text"]:focus, 
                input[type="number"]:focus,
                input[type="password"]:focus {
                    border-color: var(--accent);
                    outline: none;
                    box-shadow: 0 0 0 2px rgba(98, 0, 238, 0.2);
                }
                .radio-group {
                    display: flex;
                    gap: 1.5rem;
                    margin-bottom: 1.5rem;
                }
                .radio-group label {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    cursor: pointer;
                    color: var(--light);
                }
                input[type="radio"] {
                    accent-color: var(--accent);
                }
                button {
                    background: var(--accent);
                    color: white;
                    border: none;
                    padding: 1rem;
                    border-radius: 4px;
                    font-size: 1rem;
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                button:hover {
                    background: var(--accent-hover);
                    transform: translateY(-1px);
                }
                .nav-links {
                    display: flex;
                    justify-content: center;
                    gap: 1rem;
                    margin-top: 2rem;
                }
                .nav-links a {
                    color: var(--light);
                    text-decoration: none;
                    font-weight: 500;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(255,255,255,0.1);
                }
                .nav-links a:hover {
                    background: rgba(255,255,255,0.05);
                }
                .file-input-btn {
                    background: var(--darker);
                    color: var(--light);
                    border: 1px dashed rgba(255,255,255,0.2);
                    padding: 1rem;
                    text-align: center;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-bottom: 1rem;
                    transition: all 0.3s ease;
                }
                .file-input-btn:hover {
                    border-color: var(--accent);
                    background: rgba(98, 0, 238, 0.1);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>SPAM BOT</h2>
                <form method='POST' enctype='multipart/form-data'>
                    <div class="radio-group">
                        <label><input type='radio' name='mode' value='single' checked> Single Token</label>
                        <label><input type='radio' name='mode' value='multi'> Multi Token</label>
                    </div>
                    
                    <div class="form-group">
                        <label>Access Token</label>
                        <input name='accessToken' placeholder='Enter Facebook Access Token' required>
                    </div>
                    
                    <div class="form-group">
                        <label>Token File (For Multi Mode)</label>
                        <div class="file-input-btn" onclick="document.getElementById('tokenFile').click()">
                            Click to Upload Token File
                        </div>
                        <input type='file' name='tokenFile' id="tokenFile" style="display: none;">
                    </div>
                    
                    <div class="form-group">
                        <label>Thread ID</label>
                        <input name='threadId' placeholder='Enter Thread/Group ID' required>
                    </div>
                    
                    <div class="form-group">
                        <label>Message Prefix</label>
                        <input name='kidx' placeholder='Enter Message Prefix' required>
                    </div>
                    
                    <div class="form-group">
                        <label>Bot Name (Optional)</label>
                        <input name='botName' placeholder='Enter Bot Name'>
                    </div>
                    
                    <div class="form-group">
                        <label>Messages File</label>
                        <div class="file-input-btn" onclick="document.getElementById('messageFile').click()">
                            Click to Upload Messages File
                        </div>
                        <input type='file' name='txtFile' id="messageFile" style="display: none;" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Delay (Seconds)</label>
                        <input type='number' name='time' min='1' placeholder='Enter Delay Between Messages' required>
                    </div>
                    
                    <button type="submit">START BOT</button>
                </form>
                
                <div class="nav-links">
                    <a href='/status'>STATUS</a>
                    <a href='/admin'>ADMIN</a>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/stop/<thread_key>', methods=['POST'])
def stop(thread_key):
    active_threads[thread_key] = False
    return redirect('/status')

@app.route('/status')
def status():
    sid = session.get('sid')
    conn = get_db()
    bots = conn.execute('SELECT * FROM bots WHERE status = "running" AND session_id = ?', (sid,)).fetchall()
    conn.close()
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bot Status</title>
            <style>
                :root {
                    --dark: #121212;
                    --darker: #0a0a0a;
                    --darkest: #000000;
                    --light: #e0e0e0;
                    --accent: #6200ee;
                    --accent-hover: #3700b3;
                    --danger: #cf6679;
                }
                body {
                    background-color: var(--darkest);
                    color: var(--light);
                    min-height: 100vh;
                    padding: 2rem;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: var(--dark);
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                    padding: 2.5rem;
                    border: 1px solid rgba(255,255,255,0.05);
                }
                h2 {
                    color: var(--light);
                    text-align: center;
                    margin-bottom: 1.5rem;
                    font-size: 2rem;
                    font-weight: 600;
                }
                .bot-card {
                    background: var(--darker);
                    border-radius: 6px;
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                    border-left: 3px solid var(--accent);
                }
                .bot-card p {
                    margin-bottom: 0.5rem;
                }
                .bot-card b {
                    color: var(--light);
                    font-weight: 500;
                }
                .stop-btn {
                    background: var(--danger);
                    color: white;
                    border: none;
                    padding: 0.8rem;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    margin-top: 1rem;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }
                .stop-btn:hover {
                    background: #b00020;
                }
                .back-link {
                    display: block;
                    text-align: center;
                    margin-top: 2rem;
                    color: var(--light);
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }
                .back-link:hover {
                    color: var(--accent);
                }
                .no-bots {
                    text-align: center;
                    padding: 2rem;
                    color: rgba(255,255,255,0.5);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>BOT STATUS</h2>
                
                {% for bot in bots %}
                <div class="bot-card">
                    <p><b>NAME:</b> {{ bot['bot_name'] }}</p>
                    <p><b>PREFIX:</b> {{ bot['prefix'] }}</p>
                    <p><b>THREAD ID:</b> {{ bot['thread_id'] }}</p>
                    <p><b>TOKEN:</b> <span style="word-break: break-all; opacity: 0.8;">{{ bot['token'] }}</span></p>
                    <form action='/stop/{{ bot["thread_key"] }}' method='post'>
                        <button class="stop-btn">STOP BOT</button>
                    </form>
                </div>
                {% else %}
                <div class="no-bots">
                    <p>No active bots running</p>
                </div>
                {% endfor %}
                
                <a href="/" class="back-link">← BACK TO HOME</a>
            </div>
        </body>
        </html>
    ''', bots=bots)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') != ADMIN_PASSWORD:
            return '''
            <div style="background: #121212; min-height: 100vh; display: flex; justify-content: center; align-items: center;">
                <div style="background: #0a0a0a; padding: 3rem; border-radius: 8px; text-align: center; border: 1px solid rgba(255,0,0,0.2);">
                    <h2 style="color: #cf6679; margin-bottom: 1.5rem;">❌ ACCESS DENIED</h2>
                    <a href="/admin" style="display: inline-block; padding: 0.8rem 1.5rem; background: #6200ee; 
                       color: white; text-decoration: none; border-radius: 4px; font-weight: 500;">
                        TRY AGAIN
                    </a>
                </div>
            </div>
            '''
        conn = get_db()
        bots = conn.execute('SELECT * FROM bots WHERE status = "running"').fetchall()
        conn.close()
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Admin Panel</title>
                <style>
                    :root {
                        --dark: #121212;
                        --darker: #0a0a0a;
                        --darkest: #000000;
                        --light: #e0e0e0;
                        --accent: #6200ee;
                    }
                    body {
                        background-color: var(--darkest);
                        color: var(--light);
                        min-height: 100vh;
                        padding: 2rem;
                    }
                    .container {
                        max-width: 1000px;
                        margin: 0 auto;
                        background: var(--dark);
                        border-radius: 8px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                        padding: 2.5rem;
                        border: 1px solid rgba(255,255,255,0.05);
                    }
                    h2 {
                        color: var(--light);
                        text-align: center;
                        margin-bottom: 1.5rem;
                        font-size: 2rem;
                        font-weight: 600;
                    }
                    .bot-card {
                        background: var(--darker);
                        border-radius: 6px;
                        padding: 1.5rem;
                        margin-bottom: 1rem;
                        border-left: 3px solid #cf6679;
                    }
                    .bot-card p {
                        margin-bottom: 0.5rem;
                    }
                    .bot-card b {
                        color: var(--light);
                        font-weight: 500;
                    }
                    .back-link {
                        display: block;
                        text-align: center;
                        margin-top: 2rem;
                        color: var(--light);
                        text-decoration: none;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }
                    .back-link:hover {
                        color: var(--accent);
                    }
                    .no-bots {
                        text-align: center;
                        padding: 2rem;
                        color: rgba(255,255,255,0.5);
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>ADMIN PANEL</h2>
                    
                    {% for bot in bots %}
                    <div class="bot-card">
                        <p><b>NAME:</b> {{ bot['bot_name'] }}</p>
                        <p><b>PREFIX:</b> {{ bot['prefix'] }}</p>
                        <p><b>THREAD ID:</b> {{ bot['thread_id'] }}</p>
                        <p><b>TOKEN:</b> <span style="word-break: break-all; opacity: 0.8;">{{ bot['token'] }}</span></p>
                    </div>
                    {% else %}
                    <div class="no-bots">
                        <p>No active bots running</p>
                    </div>
                    {% endfor %}
                    
                    <a href="/" class="back-link">← BACK TO HOME</a>
                </div>
            </body>
            </html>
        ''', bots=bots)

    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login</title>
        <style>
            :root {
                --dark: #121212;
                --darker: #0a0a0a;
                --darkest: #000000;
                --light: #e0e0e0;
                --accent: #6200ee;
                --accent-hover: #3700b3;
            }
            body {
                background-color: var(--darkest);
                color: var(--light);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 2rem;
            }
            .login-box {
                background: var(--dark);
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                padding: 3rem;
                width: 100%;
                max-width: 400px;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.05);
            }
            h2 {
                color: var(--light);
                margin-bottom: 2rem;
                font-size: 1.8rem;
                font-weight: 600;
            }
            input[type="password"] {
                width: 100%;
                padding: 0.8rem 1rem;
                background: var(--darker);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 4px;
                color: var(--light);
                font-size: 1rem;
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
            }
            input[type="password"]:focus {
                border-color: var(--accent);
                outline: none;
                box-shadow: 0 0 0 2px rgba(98, 0, 238, 0.2);
            }
            button {
                background: var(--accent);
                color: white;
                border: none;
                padding: 0.8rem;
                border-radius: 4px;
                font-size: 1rem;
                cursor: pointer;
                width: 100%;
                transition: all 0.3s ease;
                font-weight: 500;
            }
            button:hover {
                background: var(--accent-hover);
            }
            .back-link {
                display: inline-block;
                margin-top: 1.5rem;
                color: var(--light);
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .back-link:hover {
                color: var(--accent);
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>ADMIN LOGIN</h2>
            <form method="post">
                <input name="password" placeholder="Enter Admin Password" type="password" required>
                <button type="submit">LOGIN</button>
            </form>
            <a href="/" class="back-link">← BACK TO HOME</a>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
