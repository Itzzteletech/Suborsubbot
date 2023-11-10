import praw
import time

# Reddit API credentials
client_id = 'your_client_id'
client_secret = 'your_client_secret'
username = 'your_username'
password = 'your_password'
user_agent = 'your_user_agent'

# Connect to Reddit
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     username=username,
                     password=password,
                     user_agent=user_agent)

# Subreddit to monitor
subreddit_name = 'your_subreddit'
subreddit = reddit.subreddit(subreddit_name)

# Phrase to look for in comments
target_phrase = 'your_target_phrase'

# Run the bot
def run_bot():
    print(f'Bot is monitoring r/{subreddit_name}')

    for comment in subreddit.stream.comments(skip_existing=True):
        if target_phrase in comment.body:
            # Do something with the comment
            # For example, reply to the comment with a message promoting your YouTube channel
            reply_message = "Thanks for using the bot! If you find it helpful, consider checking out my YouTube channel for more content. Don't forget to subscribe!"
            comment.reply(reply_message)

            # Log the comment ID to avoid processing it again
            with open('processed_comments.txt', 'a') as file:
                file.write(comment.id + '\n')

            # Check if the user is already a subscriber
            # You would need to implement your own logic to check the user's subscription status
            if not user_is_subscribed(comment.author):
                # If not subscribed, continue encouraging the user to subscribe
                while not user_is_subscribed(comment.author):
                    print(f"{comment.author} hasn't subscribed yet. Waiting...")
                    time.sleep(60)  # Wait for 60 seconds before checking again

                # If subscribed, acknowledge and continue
                print(f"{comment.author} has subscribed. Continuing bot operations.")

while True:
    try:
        run_bot()
    except Exception as e:
        print(f'An error occurred: {e}')
        # Sleep for a while before retrying
        time.sleep(60)
