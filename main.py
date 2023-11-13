import praw
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# Reddit API credentials
reddit_client_id = 'your_reddit_client_id'
reddit_client_secret = 'your_reddit_client_secret'
reddit_username = 'your_reddit_username'
reddit_password = 'your_reddit_password'
reddit_user_agent = 'your_reddit_user_agent'

# Connect to Reddit
reddit = praw.Reddit(client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     username=reddit_username,
                     password=reddit_password,
                     user_agent=reddit_user_agent)

# Subreddit to monitor
subreddit_name = 'your_subreddit'
subreddit = reddit.subreddit(subreddit_name)

# Phrase to look for in comments
target_phrase = 'your_target_phrase'

# Placeholder for a simple database or record-keeping mechanism
subscribed_users = set()

# Function to check if a user is subscribed
def user_is_subscribed(user):
    # Implement your logic to check if the user has subscribed to another user's channel
    # Example: You might want to use the YouTube API for this verification
    # Replace 'your_api_key' with your actual YouTube API key
    api_key = 'your_api_key'
    channel_id = 'user_channel_id_to_check'
    check_subscription_url = f'https://www.googleapis.com/youtube/v3/subscriptions?part=id&channelId={channel_id}&key={api_key}'

    # Make a request to the YouTube API
    response = requests.get(check_subscription_url)
    
    # Check if the user is subscribed based on the API response
    return response.status_code == 200  # Adjust this based on your API response

# Telegram Bot Token
TELEGRAM_TOKEN = 'your_telegram_token'

# YouTube API Key and Channel ID
YOUTUBE_API_KEY = 'your_youtube_api_key'
CHANNEL_ID = 'your_youtube_channel_id'

# Set up YouTube API
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("To use this bot, please subscribe to our YouTube channel first.")

def check_subscription(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Check YouTube subscription status here using the YouTube API
    is_subscribed = user_is_subscribed(user_id)

    if is_subscribed:
        update.message.reply_text("Thank you for subscribing! You can now use the bot.")
    else:
        update.message.reply_text("Please subscribe to our YouTube channel first.")

def run_bot():
    print(f'Bot is monitoring r/{subreddit_name}')

    for comment in subreddit.stream.comments(skip_existing=True):
        if target_phrase in comment.body:
            # Check if the user is already a subscriber
            if not user_is_subscribed(comment.author):
                # If not subscribed, prompt the user to subscribe to another user's channel
                comment.reply("To use this bot, subscribe to another user's channel, and another user will subscribe to yours.")
                
                # Log the comment ID to avoid processing it again
                with open('processed_comments.txt', 'a') as file:
                    file.write(comment.id + '\n')

                # Wait for the user to subscribe and update the subscribed users set
                while not user_is_subscribed(comment.author):
                    print(f"{comment.author} hasn't subscribed yet. Waiting...")
                    time.sleep(60)  # Wait for 60 seconds before checking again

                # Acknowledge and continue
                print(f"{comment.author} has subscribed. Continuing bot operations.")
                subscribed_users.add(comment.author)

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check_subscription", check_subscription))
    
    updater.start_polling()

    # Run the Reddit bot in parallel
    while True:
        try:
            run_bot()
        except Exception as e:
            print(f'An error occurred: {e}')
            # Sleep for a while before retrying
            time.sleep(60)

    updater.idle()

if __name__ == '__main__':
    main()
