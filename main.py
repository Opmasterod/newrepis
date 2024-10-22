import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import requests
from datetime import datetime
import asyncio

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the bot with your token
TELEGRAM_TOKEN = '7810054325:AAFvx1KMUvRo2MewEb3CrHgvhotwd7JFaC0'

application = Application.builder().token(TELEGRAM_TOKEN).build()

# Dictionary to store emails and passwords
email_password_map = {}
channel_id = None

# Step 1: Start command
async def start(update: Update, context):
    logger.info(f"Received /start command from {update.effective_user.id}")
    await update.message.reply_text("Please enter your channel ID in the format:\n\n-1009876543210")

# Step 2: Message handler to collect channel ID and check admin status
async def handle_message(update: Update, context):
    global channel_id
    logger.info(f"Received message: {update.message.text} from {update.effective_user.id}")

    if channel_id is None:
        channel_id = update.message.text.strip()

        try:
            chat_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            if chat_member.status in ['administrator', 'creator']:
                await update.message.reply_text("The bot is an admin in the channel. Now, please enter the emails and passwords in this format:\n\nEmail1:Pass1\nEmail2:Pass2")
            else:
                await update.message.reply_text("The bot is not an admin in the channel. Please make the bot an admin and try again.")
                channel_id = None  # Reset channel ID
        except Exception as e:
            logger.error(f"Error checking channel: {e}")
            await update.message.reply_text(f"Failed to check channel. Make sure the ID is correct and the bot has access. Error: {e}")
            channel_id = None  # Reset channel ID
    else:
        # Handle email and password list input
        try:
            email_password_list = update.message.text.split('\n')
            for item in email_password_list:
                email, password = item.split(':')
                email_password_map[email] = password.strip()

            keyboard = [[InlineKeyboardButton("Confirm to Check Emails", callback_data="confirm_check")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text("Emails and passwords have been saved. Click the button below to start checking services.", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error processing email/password input: {e}")
            await update.message.reply_text("There was an error processing your email and password list. Please ensure the format is correct.")

# Step 3: Handle button click for confirmation
async def handle_confirm_check(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Checking services for the provided emails...")

    message = await context.bot.send_message(chat_id=channel_id, text="Checking services for all emails...")

    while True:
        status_report = await get_all_service_statuses()
        await message.edit_text(status_report)
        await asyncio.sleep(100)

# The rest of your existing bot code remains unchanged...

# Add handlers to application
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(handle_confirm_check, pattern="confirm_check"))

# Start the bot
if __name__ == "__main__":
    logger.info("Bot is starting...")
    application.run_polling()
