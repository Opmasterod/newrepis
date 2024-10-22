from flask import Flask
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime
import asyncio

app = Flask(__name__)

# Flask route for health check
@app.route('/')
def health_check():
    return "Bot is running!"

# Initialize the bot with your token
TELEGRAM_TOKEN = '7810054325:AAFvx1KMUvRo2MewEb3CrHgvhotwd7JFaC0'
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Dictionary to store emails and passwords
email_password_map = {}
channel_id = None

# Step 1: Start command
async def start(update: Update, context):
    await update.message.reply_text("Please enter your channel ID in the format:\n\n-1009876543210")

# Step 2: Handle incoming messages
async def handle_message(update: Update, context):
    global channel_id

    if channel_id is None:
        channel_id = update.message.text.strip()

        try:
            chat_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            if chat_member.status in ['administrator', 'creator']:
                await update.message.reply_text("The bot is an admin in the channel. Now, please enter the emails and passwords in this format:\n\nEmail1:Pass1\nEmail2:Pass2")
            else:
                await update.message.reply_text("The bot is not an admin in the channel. Please make the bot an admin and try again.")
                channel_id = None
        except Exception as e:
            await update.message.reply_text(f"Failed to check channel. Error: {e}")
            channel_id = None
    else:
        email_password_list = update.message.text.split('\n')
        for item in email_password_list:
            email, password = item.split(':')
            email_password_map[email] = password.strip()

        keyboard = [[InlineKeyboardButton("Confirm to Check Emails", callback_data="confirm_check")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Emails and passwords have been saved. Click the button below to start checking services.", reply_markup=reply_markup)

# Step 3: Handle button click for confirmation
async def handle_confirm_check(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Checking services for the provided emails...")

    message = await context.bot.send_message(chat_id=channel_id, text="Checking services for all emails...")

    while True:
        status_report = await get_all_service_statuses()
        await message.edit_text(status_report)
        await asyncio.sleep(10)

# Step 4: Get all service statuses
async def get_all_service_statuses():
    status_report = "Service status updates for all emails:\n\n"
    for number, (email, password) in enumerate(email_password_map.items(), start=1):
        service_status = await login_and_check_status(email, password, number)
        status_report += f"{number}. {service_status}\n\n"
    return status_report

# Step 5: Login process
async def login_and_check_status(email: str, password: str, number: int):
    login_url = "https://app.koyeb.com/v1/account/login"
    login_data = {"email": email, "password": password}
    response = requests.post(login_url, json=login_data)

    if response.status_code == 200:
        response_data = response.json()
        token = response_data['token']['id']
        headers = {"Authorization": f"Bearer {token}"}
        app_url = "https://app.koyeb.com/v1/apps?limit=100"
        app_response = requests.get(app_url, headers=headers)

        if app_response.status_code == 200:
            app_data = app_response.json()
            apps = app_data.get("apps", [])
            if apps:
                latest_app = apps[0]
                app_name = latest_app.get('name', 'Unknown')
                app_status = latest_app.get('status', 'Unknown')
                domain_info = latest_app.get('domains', [])
                if domain_info:
                    service_url = f"https://{domain_info[0].get('name', 'N/A')}"
                else:
                    service_url = 'N/A'
                operational_status = await check_service_url(service_url)
                last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return (f"Email: {email}\nName: {app_name}\nURL: {service_url}\n"
                        f"Status: {app_status}\nOperational: {operational_status}\n"
                        f"Last Checked: {last_checked}")
            else:
                return f"Email: {email}\nNo apps found."
        else:
            return f"Email: {email}\nFailed to retrieve apps. Status code: {app_response.status_code}"
    else:
        return f"Email: {email}\nLogin failed. Status code: {response.status_code}"

# Step 6: Check service URL
async def check_service_url(service_url: str):
    if service_url == 'N/A':
        return "N/A (No URL available)"
    
    try:
        response = requests.get(service_url, timeout=5)
        return "Working" if response.status_code == 200 else f"Not working (HTTP {response.status_code})"
    except requests.RequestException:
        return "Not working (No response)"

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(handle_confirm_check, pattern="confirm_check"))

# Start the bot
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)  # Start Flask server

    # Run the bot
    application.run_polling()
