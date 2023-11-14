import praw
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# ... (Other imports)

# Set up Reddit and YouTube API (same as before)

# Database to store user-submitted YouTube channels and confirmation status
user_channels = {}

# Set up a timestamp to track the last subscription time
last_subscription_time = {}

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
        context.user_data['submitting_channel'] = 
      True

# Telegram message handler - handle submitted channel link
def handle_channel_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reddit_username = update.message.from_user.username

    if 'submitting_channel' in context.user_data:
        channel_link = update.message.text

        # Store the submitted channel link in the database
        user_channels[user_id] = {'link': channel_link, 'confirmed': False}

        # Ask the user to confirm their subscription
        update.message.reply_text("Thank you! Your channel link has been recorded. Please confirm that you have subscribed by typing /confirm_subscription.")
        del context.user_data['submitting_channel']
    else:
        update.message.reply_text("Sorry, I wasn't expecting a channel link at this time. If you want to submit your channel, use /submit_channel.")

# Telegram command handler - confirm_subscription
def confirm_subscription(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in user_channels and not user_channels[user_id]['confirmed']:
        # Check if the user has confirmed their subscription
        if user_is_subscribed(user_id):
            user_channels[user_id]['confirmed'] = True
            update.message.reply_text("Thank you for confirming your subscription! You can now use the bot.")
        else:
            update.message.reply_text("Please confirm your subscription by subscribing to our YouTube channel.")
    else:
        update.message.reply_text("You have already confirmed your subscription or haven't submitted your channel. Use /submit_channel to submit your channel.")

# Telegram command handler - subscribe
def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reddit_username = update.message.from_user.username

    if is_owner(reddit_username):
        update.message.reply_text("You are the owner. No need to subscribe to others.")
    elif user_id in last_subscription_time and time.time() - last_subscription_time[user_id] < 20:
        update.message.reply_text("Please wait for 20 seconds before subscribing to another channel.")
    elif user_id in user_channels:
        # Get the channel to subscribe to
        channel_to_subscribe = user_channels[user_id]['link']

        # Subscribe to the selected channel
        # You might want to add error handling here
        # to handle cases where subscription fails
        # For simplicity, the code assumes a successful subscription

        # Inform the user about the delay
        update.message.reply_text("Subscribing... Please note that YouTube may have restrictions on subscribing to channels too quickly. This process may take a moment.")

        # Simulate the subscription process
        # In a real bot, you would use the YouTube API to subscribe to the channel
        time.sleep(5)  # Simulate the subscription process taking 5 seconds

        # Update the last subscription time
        last_subscription_time[user_id] = time.time()

        # Acknowledge and continue
        update.message.reply_text(f"Successfully subscribed to {channel_to_subscribe}! You can now use the bot.")
    else:
        update.message.reply_text("Please submit your channel using /submit_channel before subscribing to another channel.")

# ... (Other parts of your code)

if __name__ == '__main__':
    # Start both bots (Telegram and Reddit)
    while True:
        try:
            run_reddit_bot()
        except Exception as e:
            print(f'Reddit bot error: {e}')
            time.sleep(60)  # Sleep before retrying

        main_telegram()
