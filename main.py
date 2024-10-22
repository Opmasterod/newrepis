from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import requests
from datetime import datetime
import asyncio

# Initialize the bot with your token
TELEGRAM_TOKEN = '7810054325:AAFvx1KMUvRo2MewEb3CrHgvhotwd7JFaC0'

application = Application.builder().token(TELEGRAM_TOKEN).build()

# Dictionary to store emails and passwords
email_password_map = {}
channel_id = None

# Step 1: Start command
async def start(update: Update, context):
    # Ask for channel ID input
    await update.message.reply_text("Please enter your channel ID in the format:\n\n-1009876543210")

# Step 2: Message handler to collect channel ID and check admin status
async def handle_message(update: Update, context):
    global channel_id

    # Check if channel ID is not set, then expect the channel ID as input
    if channel_id is None:
        channel_id = update.message.text.strip()

        try:
            # Check if the bot is an admin in the provided channel
            chat_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            if chat_member.status in ['administrator', 'creator']:
                await update.message.reply_text("The bot is an admin in the channel. Now, please enter the emails and passwords in this format:\n\nEmail1:Pass1\nEmail2:Pass2")
            else:
                await update.message.reply_text("The bot is not an admin in the channel. Please make the bot an admin and try again.")
                channel_id = None  # Reset channel ID
        except Exception as e:
            await update.message.reply_text(f"Failed to check channel. Make sure the ID is correct and the bot has access. Error: {e}")
            channel_id = None  # Reset channel ID
    else:
        # If channel ID is set, then expect the email and password list
        email_password_list = update.message.text.split('\n')
        for item in email_password_list:
            email, password = item.split(':')
            email_password_map[email] = password.strip()

        # Display a button to confirm checking
        keyboard = [[InlineKeyboardButton("Confirm to Check Emails", callback_data="confirm_check")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Emails and passwords have been saved. Click the button below to start checking services.", reply_markup=reply_markup)

# Step 3: Handle button click for confirmation
async def handle_confirm_check(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Confirm message and start checking services
    await query.edit_message_text("Checking services for the provided emails...")

    # Initial message to check services
    message = await context.bot.send_message(chat_id=channel_id, text="Checking services for all emails...")

    while True:
        status_report = await get_all_service_statuses()
        # Edit the message in the channel with the updated status
        await message.edit_text(status_report)

        # Wait for 10 seconds before checking again
        await asyncio.sleep(600)

# Step 4: Get all service statuses and format the result
async def get_all_service_statuses():
    status_report = "Service status updates for all emails:\n\n"
    for number, (email, password) in enumerate(email_password_map.items(), start=1):
        # Fetch service details for each email and add numbering
        service_status = await login_and_check_status(email, password, number)
        status_report += f"{number}. {service_status}\n\n"
    return status_report

# Step 5: Login process and fetching service status
async def login_and_check_status(email: str, password: str, number: int):
    login_url = "https://app.koyeb.com/v1/account/login"
    login_data = {"email": email, "password": password}

    # Send POST request to login
    response = requests.post(login_url, json=login_data)

    if response.status_code == 200:
        response_data = response.json()
        token = response_data['token']['id']

        # Use the token to get the app list
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

                # Check if the service URL is working
                operational_status = await check_service_url(service_url)

                # If both conditions are met, service is healthy and running
                healthy_and_running = "Service is healthy and running" if app_status == 'HEALTHY' and operational_status == 'Working' else "Service status unknown"

                # Format the service details for this email
                last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp
                status_message = (f"Email: {email}\n"
                                  f"Name: {app_name}\n"
                                  f"URL of Service: {service_url}\n"
                                  f"Status: {app_status}\n"
                                  f"Operational: {operational_status}\n"
                                  f"{healthy_and_running}\n"
                                  f"Last Checked by Bot: {last_checked}\n"
                                  f"STATUS: {app_status.upper()}\n"
                                  f"STATUS: {operational_status.upper()}")
                return status_message
            else:
                return f"Email: {email}\nNo apps found."
        else:
            return f"Email: {email}\nFailed to retrieve apps. Status code: {app_response.status_code}"
    else:
        return f"Email: {email}\nLogin failed. Status code: {response.status_code}. Please check your credentials."

# Step 6: Function to check if the service URL is operational
async def check_service_url(service_url: str):
    if service_url == 'N/A':
        return "N/A (No URL available)"
    
    try:
        response = requests.get(service_url, timeout=5)
        if response.status_code == 200:
            return "Working"
        else:
            return f"Not working (HTTP {response.status_code})"
    except requests.RequestException:
        return "Not working (No response)"

# Add handlers to application
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(handle_confirm_check, pattern="confirm_check"))

# Start the bot
application.run_polling()
