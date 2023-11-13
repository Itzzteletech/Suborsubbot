import praw
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# Reddit API credentials
reddit_client_id = 'your_reddit_client_id'
reddit_client_secret = 'your_reddit_client_secret'
reddit_username = 'your_reddit_username'
reddit_password = 'your_reddit_password'
reddit_user_agent = 'your_reddit_user_agent'

# Telegram Bot Token
TELEGRAM_TOKEN = 'your_telegram_token'

# YouTube API Key and Channel ID
YOUTUBE_API_KEY = 'your_youtube_api_key'
CHANNEL_ID = 'your_youtube_channel_id'

# Your Reddit username (owner)
OWNER_REDDIT_USERNAME = 'your_reddit_username'

# Set up Reddit
reddit = praw.Reddit(client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     username=reddit_username,
                     password=reddit_password,
                     user_agent=reddit_user_agent)

# Set up YouTube API
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Database to store user-submitted YouTube channels
user_channels = {}

# Function to check if a user is the owner (you)
def is_owner(username):
    return username.lower() == OWNER_REDDIT_USERNAME.lower()

# Function to check if a user is subscribed
def user_is_subscribed(user_id):
    try:
        # Call the YouTube API to check subscription status
        subscriptions = youtube.subscriptions().list(part='snippet', channelId=CHANNEL_ID, mine=True).execute()
        subscribed_channels = [item['snippet']['resourceId']['channelId'] for item in subscriptions.get('items', [])]

        return CHANNEL_ID in subscribed_channels

    except HttpError as e:
        print(f"Error checking YouTube subscription: {e}")
        return False

# Telegram command handler - start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! To check your subscription status, use /check_subscription. To submit your YouTube channel link, use /submit_channel.")

# Telegram command handler - check_subscription
def check_subscription(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reddit_username = update.message.from_user.username

    if is_owner(reddit_username):
        update.message.reply_text("You are the owner. No need to check subscription.")
    else:
        # Check YouTube subscription status
        is_subscribed = user_is_subscribed(user_id)

        if is_subscribed:
            update.message.reply_text("Thank you for subscribing! You can now use the bot.")
        else:
            update.message.reply_text("Please subscribe to our YouTube channel first.")

# Telegram command handler - submit_channel
def submit_channel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reddit_username = update.message.from_user.username

    if is_owner(reddit_username):
        update.message.reply_text("You are the owner. No need to submit a channel.")
    else:
        update.message.reply_text("Please provide your YouTube channel link.")

        # Save the state to identify user and store their YouTube channel link
        context.user_data['submitting_channel'] = True

# Telegram message handler - handle submitted channel link
def handle_channel_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reddit_username = update.message.from_user.username

    if 'submitting_channel' in context.user_data:
        channel_link = update.message.text

        # Store the submitted channel link in the database
        user_channels[user_id] = channel_link

        update.message.reply_text("Thank you! Your channel link has been recorded.")
        del context.user_data['submitting_channel']
    else:
        update.message.reply_text("Sorry, I wasn't expecting a channel link at this time. If you want to submit your channel, use /submit_channel.")

# Telegram command handler - subscribe
def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reddit_username = update.message.from_user.username

    if is_owner(reddit_username):
        update.message.reply_text("You are the owner. No need to subscribe to others.")
    else:
        # Get a list of other users' channels (excluding the user and already subscribed channels)
        other_channels = {u: c for u, c in user_channels.items() if u != user_id and not user_is_subscribed(u)}

        if other_channels:
            # Create an inline keyboard with buttons for each channel
            keyboard = [[InlineKeyboardButton(f'{u}\'s Channel', url=c)] for u, c in other_channels.items()]
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text("Choose a channel to subscribe:", reply_markup=reply_markup)
        else:
            update.message.reply_text("No available channels to subscribe at the moment.")
# Telegram callback query handler - handle inline button clicks
def button_click(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    query = update.callback_query

    # Extract the user ID and channel link from the button text
    user_to_subscribe = int(query.data.split(':')[0])
    channel_to_subscribe = user_channels[user_to_subscribe]

    # Subscribe to the selected
