
import os
import tempfile
import pyimgur
import requests
from flask import jsonify

# Imgur Client ID, Instagram user ID, and Access Token
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "your_imgur_client_id")
IG_USER_ID = os.getenv("IG_USER_ID", "your_instagram_user_id")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "your_access_token")


# Upload to Imgur
def upload_to_imgur(local_file_path):
    try:
        im = pyimgur.Imgur(IMGUR_CLIENT_ID)
        uploaded_image = im.upload_image(local_file_path, title="Uploaded via CF")
        return uploaded_image.link
    except Exception as e:
        print(f"Failed to upload to Imgur: {e}")
        return None


# Upload to Instagram
def upload_media_to_instagram(image_url, caption):
    url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    params = {"image_url": image_url, "caption": caption, "access_token": INSTAGRAM_ACCESS_TOKEN}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"Failed to upload media: {response.json()}")
        return None


# Publish Media
def publish_media(media_id):
    url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    params = {"creation_id": media_id, "access_token": INSTAGRAM_ACCESS_TOKEN}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return "Media published successfully!"
    else:
        return f"Failed to publish media: {response.json()}"


# Google Cloud Function Handler
def post_to_instagram_via_api(request):
    try:
        # Handle CORS for preflight OPTIONS request
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)

        if request.method != 'POST':
            return jsonify({"success": False, "message": "Only POST requests are allowed"}), 405

        # Parse form data
        caption = request.form.get('caption')
        file = request.files.get('media')
        if not file or not caption:
            return jsonify({"success": False, "message": "Missing caption or media file"}), 400

        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_path = temp_file.name
            file.save(file_path)

        # Upload the image to Imgur
        uploaded_image_url = upload_to_imgur(file_path)
        os.remove(file_path)  # Clean up the temp file
        if not uploaded_image_url:
            return jsonify({"success": False, "message": "Failed to upload image to Imgur"}), 500

        # Upload media to Instagram
        media_id = upload_media_to_instagram(uploaded_image_url, caption)
        if not media_id:
            return jsonify({"success": False, "message": "Failed to upload media to Instagram"}), 500

        # Publish media on Instagram
        result = publish_media(media_id)

        headers = {'Access-Control-Allow-Origin': '*'}
        return jsonify({"success": True, "message": result}), 200, headers

    except Exception as e:
        print(f"Error: {e}")
        headers = {'Access-Control-Allow-Origin': '*'}
        return jsonify({"success": False, "message": "An unexpected error occurred", "error": str(e)}), 500, headers
