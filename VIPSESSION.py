from telethon import TelegramClient, events, Button
from datetime import datetime, timedelta
import pytz
import logging
from flask import Flask
import threading

# Configure logging for better error tracking
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your API ID, hash, and bot token
API_ID = 23844616
API_HASH = '4aeca3680a20f9b8bc669f9897d5402f'
BOT_TOKEN = '7627409273:AAH0t4LrN1HqKExugg75LIJPb1i-1V_zRLs'

# Define the channel IDs for PUBLIC and VIP messages
PUBLIC_CHANNEL_ID = -1002076005263  # Replace with your actual PUBLIC channel ID
VIP_CHANNEL_ID = -1002215575410 # Replace with your actual VIP channel ID

# Create the bot client
bot = TelegramClient('bot', API_ID, API_HASH)

# Dictionary to store user session data
user_sessions = {}

# Define currency pairs
currency_pairs = [
    "USDMXN-OTC",
    "USDBRL-OTC",
    "USDTRY-OTC",
    "USDARS-OTC",
    "USDBDT-OTC",
    "USDCOP-OTC",
    "USDEGP-OTC",
    "USDIDR-OTC",
    "USDPKR-OTC",
    "NZDCAD-OTC",
    "EURUSD-OTC",
    "EURGBP-OTC",
    "AUDUSD-OTC"
]

# Handle the /start command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        # Initialize the user session
        user_sessions[event.sender_id] = {}
        await event.respond(
            "Hello 👋🏻 Choose Your Channel For Sending The Signal",
            buttons=[
                [Button.inline("📊 PUBLIC", b"public")],
                [Button.inline("📊 VIP", b"vip")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await event.respond("An error occurred. Please try again later.")

# Handle inline button clicks
@bot.on(events.CallbackQuery)
async def callback(event):
    try:
        # Get or initialize user session
        user_session = user_sessions.get(event.sender_id, {})

        if event.data == b"vip":
            buttons = [[Button.inline(pair, f"vip_currency_{pair}".encode())] for pair in currency_pairs]
            await event.edit("Select Currency for VIP Signal", buttons=buttons)

        elif event.data == b"public":
            buttons = [[Button.inline(pair, f"public_currency_{pair}".encode())] for pair in currency_pairs]
            await event.edit("Select Currency for PUBLIC Signal", buttons=buttons)

        # Handle currency selection for VIP
        elif b"vip_currency_" in event.data:
            currency = event.data.decode().split("_")[-1]
            user_session['currency'] = currency
            user_session['channel_type'] = 'vip'

            buttons = [
                [Button.inline(
                    (datetime.now(pytz.timezone("America/Sao_Paulo")) + timedelta(minutes=i)).strftime("%H:%M:00"),
                    f"{i}_min".encode()
                )] for i in range(1, 6)
            ]
            await event.edit(f"Select Expiration Time for {currency}", buttons=buttons)

        # Handle currency selection for PUBLIC
        elif b"public_currency_" in event.data:
            currency = event.data.decode().split("_")[-1]
            user_session['currency'] = currency
            user_session['channel_type'] = 'public'

            buttons = [
                [Button.inline(
                    (datetime.now(pytz.timezone("America/Sao_Paulo")) + timedelta(minutes=i)).strftime("%H:%M:00"),
                    f"{i}_min_public".encode()
                )] for i in range(1, 6)
            ]
            await event.edit(f"Select Expiration Time for {currency}", buttons=buttons)

        # Handle expiration time selection for both VIP and PUBLIC
        elif b"_min" in event.data:
            minutes_offset = int(event.data.decode().split('_')[0])
            expiration_time = (datetime.now(pytz.timezone("America/Sao_Paulo")) + timedelta(minutes=minutes_offset)).strftime("%H:%M:00")
            user_session['expiration'] = expiration_time

            await event.edit(
                f"Select Direction for {user_session['currency']} Expiration {expiration_time}",
                buttons=[
                    [Button.inline("🟢 UP", b"direction_up")],
                    [Button.inline("🔴 DOWN", b"direction_down")]
                ]
            )

        # Handle direction selection for both VIP and PUBLIC
        elif event.data == b"direction_up" or event.data == b"direction_down":
            direction = "🟢 UP" if event.data == b"direction_up" else "🔴 DOWN"
            user_session['direction'] = direction

            currency = user_session.get('currency')
            expiration_time = user_session.get('expiration')
            channel_type = user_session.get('channel_type')

            if currency and expiration_time:
                if channel_type == 'vip':
                    message = (f"**📊 Currency:** **{currency}**\n"
                               f"**⏳ Expiration:** **M1**\n"
                               f"**⏱ Check-in:** **{expiration_time}**\n"
                               f"**↕️ Direction:** **{direction}**\n\n"
                               f"**Only FMG✅¹**")
                else:  # public
                    fmg_time = (datetime.strptime(expiration_time, "%H:%M:%S") + timedelta(minutes=1)).strftime("%H:%M:%S")
                    smg_time = (datetime.strptime(fmg_time, "%H:%M:%S") + timedelta(minutes=1)).strftime("%H:%M:%S")
                    message = (f"**📊 Currency:** **{currency}**\n"
                               f"**⏳ Expiration:** **M1**\n"
                               f"**⏱ Check-in:** **{expiration_time}**\n"
                               f"**↕️ Direction:** **{direction}**\n\n"
                               f"**✅ Check-in:** **{expiration_time}** {direction}\n\n"
                               f"**✅¹ FMG Check-in:** **{fmg_time}**\n"
                               f"**✅² SMG Check-in:** **{smg_time}**")

                user_session['formatted_message'] = message

                # Display the message with inline buttons
                await event.edit(message, buttons=[Button.inline("📊 SEND TO CHANNEL", b"send_to_channel")])

        # Handle sending message to the channel
        elif event.data == b"send_to_channel":
            channel_type = user_session.get('channel_type')
            message = user_session.get('formatted_message', "No message to send.")

            if channel_type == 'public':
                # For public messages, send to PUBLIC_CHANNEL_ID with the Quotex registration link
                await bot.send_message(PUBLIC_CHANNEL_ID, message, buttons=[
                    [Button.url("📲 Quotex Registration", "https://broker-qx.pro/sign-up/?lid=840909")]
                ])
            else:
                # For VIP messages, send to VIP_CHANNEL_ID without the Quotex link
                await bot.send_message(VIP_CHANNEL_ID, message)

            await event.edit(f"Signal sent to the {channel_type.upper()} channel.")

    except Exception as e:
        logger.error(f"Error in callback: {e}")
        await event.respond("An error occurred. Please try again later.")

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def run_bot():
    with bot:
        bot.run_until_disconnected()

if __name__ == '__main__':
    # Start the Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run the Telegram bot
    run_bot()