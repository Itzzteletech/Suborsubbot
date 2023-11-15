import logging
import sqlite3
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram Bot API token
# You can obtain this token by talking to the BotFather on Telegram.
TOKEN = 'YOUR_BOT_TOKEN'
OWNER_ID = 123456789  # Replace with your Telegram user ID

# Connect to SQLite database
conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

# Create a table to store subscriptions
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER,
        channel_link TEXT
    )
''')
conn.commit()

# Dictionary to store last subscribe time for each user
last_subscribe_time = {}

# Set to store channels the bot is subscribed to
bot_subscriptions = set()

# Dictionary to store blocked users and their unsubscription timestamp
blocked_users = {}

# Bot states
START, SUBSCRIBE, JOIN_CHANNEL, JOIN_GROUP = range(4)

# Handler for /start command
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} started the conversation.")
    
    # Check if the user is the owner
    if user_id == OWNER_ID:
        update.message.reply_text("You are the owner. You cannot subscribe.")
        return ConversationHandler.END
    
    # Check if the bot is already subscribed
    if user_id not in bot_subscriptions:
        update.message.reply_text("Please subscribe to the bot first before starting.")
        return ConversationHandler.END
    
    update.message.reply_text(
        "Welcome to the bot! To continue, you need to subscribe to my YouTube channel and join my Telegram channel and group.\n"
        "Click the buttons below to perform the required actions.",
        reply_markup=get_subscribe_keyboard()
    )
    return SUBSCRIBE

# Handler for YouTube subscribe button
def youtube_subscribe(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    logger.info(f"User {user_id} subscribed to the YouTube channel.")
    
    # Store the subscription in the database
    cursor.execute('INSERT INTO subscriptions (user_id, channel_link) VALUES (?, ?)', (user_id, 'YOUR_YOUTUBE_CHANNEL_URL'))
    conn.commit()

    # Update last subscribe time for the user
    last_subscribe_time[user_id] = time.time()

    # Update bot subscriptions
    if user_id == OWNER_ID:
        bot_subscriptions.add('YOUR_YOUTUBE_CHANNEL_URL')

    update.callback_query.message.reply_text(
        "Thank you for subscribing to my YouTube channel!\n"
        "Now, please join my Telegram channel and group using the buttons below.",
        reply_markup=get_join_keyboard()
    )
    return JOIN_CHANNEL

# Handler for Telegram channel join button
def telegram_channel_join(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    logger.info(f"User {user_id} joined the Telegram channel.")
    
    # Check if the user is the owner
    if user_id == OWNER_ID:
        update.callback_query.message.reply_text("You are the owner. You cannot join the channel.")
        return ConversationHandler.END

    update.callback_query.message.reply_text(
        "Great! You have joined my Telegram channel.\n"
        "To proceed, please join my Telegram group as well using the button below.",
        reply_markup=get_join_keyboard()
    )
    return JOIN_GROUP

# Handler for Telegram group join button
def telegram_group_join(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    logger.info(f"User {user_id} joined the Telegram group.")
    
    # Check if the user is the owner
    if user_id == OWNER_ID:
        update.callback_query.message.reply_text("You are the owner. You cannot join the group.")
        return ConversationHandler.END

    update.callback_query.message.reply_text(
        "Awesome! You have successfully joined my Telegram group.\n"
        "You are now eligible to use the bot.\n"
        "Feel free to ask any questions or use any commands."
    )
    return ConversationHandler.END

# Helper function to create inline keyboard for subscribing and joining
def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    subscribe_url = "https://youtube.com/@mp4editor822"  # Replace with your YouTube channel URL
    keyboard = [
        [InlineKeyboardButton("Subscribe to YouTube Channel", callback_data='subscribe')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_join_keyboard() -> InlineKeyboardMarkup:
    channel_url = "https://t.me/teletechbots"  # Replace with your Telegram channel URL
    group_url = "https://t.me/teletechbotsdiscussion_group"  # Replace with your Telegram group URL
    keyboard = [
        [InlineKeyboardButton("Join Telegram Channel", callback_data='join_channel')],
        [InlineKeyboardButton("Join Telegram Group", callback_data='join_group')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Handler for /cancel command
def cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    logger.info(f"User {user_id} cancelled the operation.")
    update.callback_query.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# Function to check for unsubscribed channels
def check_unsubscribes(context: CallbackContext):
    global bot_subscriptions

    # Fetch all subscribed channels from the database
    cursor.execute('SELECT DISTINCT channel_link FROM subscriptions WHERE user_id = ?', (OWNER_ID,))
    user_subscriptions = set([channel[0] for channel in cursor.fetchall()])

    # Check for unsubscribed channels
    unsubscribed_channels = bot_subscriptions - user_subscriptions

    if unsubscribed_channels:
        context.bot.send_message(OWNER_ID, f"Warning: You have unsubscribed from {', '.join(unsubscribed_channels)}! "
                                           f"Please subscribe to them again.")

        # Block the user if not subscribed within 150 seconds
        for channel in unsubscribed_channels:
            if user_id not in blocked_users or (datetime.now() - blocked_users[user_id]).seconds > 150:
                blocked_users[user_id] = datetime.now()
                context.bot.send_message(user_id, f"You have 150 seconds to subscribe to {channel}.")
                context.job_queue.run_once(unblock_user, 150, context=(context, user_id, channel))

    # Update bot subscriptions
    bot_subscriptions = user_subscriptions

# Function to unblock the user after the specified time
def unblock_user(context: CallbackContext):
    _, user_id, channel = context.job.context

    if user_id in blocked_users:
        del blocked_users[user_id]

        # Notify the owner about the blocke
