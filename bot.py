import os
import logging
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

from pymongo import MongoClient

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

START, SUBSCRIBE, JOIN_CHANNEL, JOIN_GROUP = range(4)

def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id == OWNER_ID:
        update.message.reply_text("You are the owner. You cannot subscribe.")
        return ConversationHandler.END

    if user_id not in bot_subscriptions:
        update.message.reply_text("Please subscribe to the bot first before starting.")
        return ConversationHandler.END

    update.message.reply_text(
        "Welcome to the bot! To continue, you need to subscribe to my YouTube channel and join my Telegram channel and group.\n"
        "Click the buttons below to perform the required actions.",
        reply_markup=get_subscribe_keyboard(),
    )
    return SUBSCRIBE

def youtube_subscribe(update: Update, context: CallbackContext) -> int:
    user_id = update.callback_query.from_user.id
    last_subscribe_time[user_id] = time.time()

    if user_id == OWNER_ID:
        bot_subscriptions.add('https://youtube.com/@Tele_Technics?si=t2eo5Tyb-cedQ9Yg')

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

def check_unsubscribes(context: CallbackContext):
    global bot_subscriptions

    unsubscribed_channels = bot_subscriptions - set([channel[0] for channel in collection.distinct("channel_link")])

    if unsubscribed_channels:
        unsubscribed_channels = [channel for channel in unsubscribed_channels if channel not in blocked_users.values()]

        if unsubscribed_channels:
            context.bot.send_message(
                OWNER_ID,
                f"Warning: You have unsubscribed from {', '.join(unsubscribed_channels)}! "
                f"Please subscribe to them again.",
            )

            for channel in unsubscribed_channels:
                for user_id, blocked_channel in blocked_users.items():
                    if (
                        blocked_channel == channel
                        and (datetime.now() - blocked_users[user_id]).seconds > 150
                    ):
                        blocked_users[user_id] = datetime.now()
                        context.bot.send_message(
                            user_id, f"You have 150 seconds to subscribe to {channel}."
                        )
                        context.job_queue.run_once(
                            unblock_user, 150, context=(context, user_id, channel)
                        )

    bot_subscriptions = set(collection.distinct("channel_link"))

def unblock_user(context: CallbackContext):
    _, user_id, channel = context.job.context

    if user_id in blocked_users:
        del blocked_users[user_id]

def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    message_text = update.message.text.split('/broadcast ', 1)[1]

    for user_id in bot_subscriptions:
        context.bot.send_message(user_id, message_text)

def unblock_user_command(update: Update, context: CallbackContext):
    # Implement unblock_user_command logic here
    pass
