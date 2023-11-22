import os
import logging
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    InlineQueryHandler,
)

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_TELEGRAM_ID"))
MONGO_URI = os.getenv("MONGODB_ATLAS_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

last_subscribe_time = {}
bot_subscriptions = set()
blocked_users = {}

START, SUBSCRIBE, JOIN_CHANNEL, JOIN_GROUP, ASK_LOGO, ASK_CHANNEL_LINK, VIEW_OTHER_CHANNELS = range(7)

def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    user_first_name = update.message.from_user.first_name

    # Welcome message with a start picture
    start_photo_file_id = "http://ddl.safone.dev/1508558/None?hash=AgADBb" # Replace with your start photo file ID
    context.bot.send_photo(chat_id=user_id, photo=start_photo_file_id, caption=f"Welcome, {user_first_name}! Thank you for using me. I'm Suborsubbot the powerful telegram bot to increase your YouTube channel Subscriptions. Any doubt send /help.")

    # Asking the user to subscribe and join
    update.message.reply_text(
        "To get started, you must subscribe to my YouTube channel and join my Telegram channel and group.\n"
        "Click the buttons below to perform the required actions.",
        reply_markup=get_subscribe_keyboard(),
    )

    return SUBSCRIBE

def youtube_subscribe(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    last_subscribe_time[user_id] = time.time()

    if user_id == OWNER_ID:
        bot_subscriptions.add('https://youtube.com/@Tele_Technics')

    update.callback_query.message.reply_text(
        "Thank you for subscribing to my YouTube channel!\n"
        "Now, please join my Telegram channel and group using the buttons below.",
        reply_markup=get_join_keyboard(),
    )
    return JOIN_CHANNEL

def telegram_channel_join(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    if user_id == OWNER_ID:
        update.callback_query.message.reply_text("You are the owner. You cannot join the channel.")
        return ConversationHandler.END

    update.callback_query.message.reply_text(
        "Great! You have joined my Telegram channel.\n"
        "To proceed, please join my Telegram group as well using the button below.",
        reply_markup=get_join_keyboard(),
    )
    return JOIN_GROUP

def telegram_group_join(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    if user_id == OWNER_ID:
        update.callback_query.message.reply_text("You are the owner. You cannot join the group.")
        return ConversationHandler.END

    update.callback_query.message.reply_text(
        "Awesome! You have successfully joined my Telegram group.\n"
        "You are now eligible to use the bot.\n"
        "Feel free to ask any questions or use any commands.",
    )
    return ConversationHandler.END

def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    subscribe_url = "https://youtube.com/@Tele_Technics?si=t2eo5Tyb-cedQ9Yg"
    keyboard = [
        [InlineKeyboardButton("Subscribe to YouTube Channel", callback_data="subscribe")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_join_keyboard() -> InlineKeyboardMarkup:
    channel_url = "https://t.me/teletechbots"
    group_url = "https://t.me/teletechbotsdiscussion_group"
    keyboard = [
        [InlineKeyboardButton("Join Telegram Channel", callback_data="join_channel")],
        [InlineKeyboardButton("Join Telegram Group", callback_data="join_group")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    update.callback_query.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def ask_logo(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    update.message.reply_text("Great! Now, please share your YouTube channel logo with me.")
    return ASK_LOGO

def receive_logo(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    logo_file_id = update.message.photo[-1].file_id
    context.user_data['logo_file_id'] = logo_file_id
    update.message.reply_text("Thank you for sharing your YouTube channel logo! Now, please provide your YouTube channel link.")
    return ASK_CHANNEL_LINK

def ask_channel_link(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    update.message.reply_text(
        "Please provide your YouTube channel link. Remember, don't just copy from YouTube. Write a unique description for your channel."
        "\n\nExample: `https://youtube.com/c/YourChannelName`"
    )
    return ASK_CHANNEL_LINK

def receive_channel_link(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    channel_link = update.message.text.strip()
    logo_file_id = context.user_data.get('logo_file_id', None)

    # Store the logo file ID and channel link in the database
    collection.update_one(
        {'user_id': user_id},
        {'$set': {'logo_file_id': logo_file_id, 'channel_link': channel_link}},
        upsert=True
    )

    update.message.reply_text("Thank you! Your YouTube channel information has been stored.")
    return ConversationHandler.END

def view_other_channels(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id

    # Get other channels' information from the database
    other_channels = collection.find({'user_id': {'$ne': user_id}}, {'logo_file_id': 1, 'channel_link': 1})

    keyboard = []

    for channel in other_channels:
        keyboard.append([InlineKeyboardButton(channel['channel_link'], callback_data=f"view_channel_{channel['_id']}")])

    keyboard.append([InlineKeyboardButton("Close", callback_data="close_subscribe")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_text("Here are other channels:", reply_markup=
