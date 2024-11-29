import os
import tempfile
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session
import tweepy
import json
from flask import Request  # If you're using Flask for your Google Cloud Function

# Load environment variables from .env (if running locally)
load_dotenv()

# Initialize API credentials
api_key = os.getenv("API_KEY")
api_key_secret = os.getenv("API_KEY_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")

# Initialize Tweepy client
client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_key_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

def upload_media(media_path):
    """
    Upload media to Twitter and return the media ID.

    Args:
        media_path (str): Path to the media file.

    Returns:
        str: Media ID if successful, None otherwise.
    """
    url = "https://upload.twitter.com/1.1/media/upload.json"
    oauth = OAuth1Session(api_key, api_key_secret, access_token, access_token_secret)

    with open(media_path, 'rb') as media_file:
        files = {'media': media_file}
        response = oauth.post(url, files=files)

        print(f"Media upload response status: {response.status_code}")
        print(f"Media upload response: {response.text}")

        if response.status_code == 200:
            return response.json().get('media_id')
    return None

def tweet_with_media(request):
    """
    Google Cloud Function to handle tweeting with media.

    Args:
        request (flask.Request): The request object.

    Returns:
        JSON response.
    """
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })

    try:
        # Debug request information
        print(f"Request Content-Type: {request.content_type}")

        # Extract tweet text and media from the request
        tweet_text = request.form.get('tweet_text')
        media = request.files.get('media')

        print(f"Tweet text: {tweet_text}")
        print(f"Media file received: {media.filename if media else 'None'}")

        # Check if tweet text and media are provided
        if not tweet_text or not media:
            return json.dumps({"error": "Tweet text or media file missing"}), 400, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }

        # Save the media file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            media_path = tmp_file.name
            media.save(media_path)

        # Upload media to Twitter
        media_id = upload_media(media_path)
        if not media_id:
            return json.dumps({"error": "Failed to upload media"}), 400, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }

        # Post the tweet with the uploaded media
        response = client.create_tweet(
            text=tweet_text,
            media_ids=[media_id]
        )

        # Return success response
        return json.dumps({
            "message": "Tweet posted successfully!",
            "tweet": response.data
        }), 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }

    except Exception as e:
        print(f"Error: {e}")
        return json.dumps({"error": str(e)}), 500, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }

