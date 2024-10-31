from dotenv import load_dotenv
import os
import tweepy
import logging

# Load environment variables
load_dotenv()

def authenticate_twitter():
    """Authenticate and return Twitter API v2 client."""
    logging.info("Function called: authenticate_twitter()")
    
    # Load Twitter API credentials from environment variables
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    
    logging.info("Function authenticate_twitter() returned: Twitter API v2 client")
    return client

def send_tweet(context_variables, tweet_content: str):
    """
    Send a tweet using the authenticated user's account. The content should be less than 280 characters and can include hashtags, mentions, and URLs.

    Args:
        context_variables (dict): A dictionary containing context information.
        tweet_content (str): The content of the tweet to be sent.
    """
    logging.info(f"Function called: send_tweet(context_variables={context_variables}, tweet_content='{tweet_content[:20]}...')")
    
    client = authenticate_twitter()
    try:
        response = client.create_tweet(text=tweet_content)
        result = f"<result><message>Tweet sent successfully. Tweet ID: {response.data['id']}</message></result>"
        logging.info(f"Function send_tweet() returned: {result}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error sending tweet: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message
