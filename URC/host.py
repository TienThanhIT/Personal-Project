from flask import Flask
from threading import Thread
import os 
import logging

# Set up logging for the host server
logging.basicConfig(level=logging.INFO)

# Create the Flask app instance
app = Flask(__name__)

# Define the root route (this is what the host pings)
@app.route('/')
def home():
    # Return a simple status message
    return "Bot is awake and running!"

# Function to run the Flask server in a separate thread
def run():
    # 1. Get the port from the environment variable 'PORT'
    # 2. Use a fallback (10000) if 'PORT' is not set
    port = int(os.environ.get("PORT", 10000))
    
    # host='0.0.0.0' is required for cloud hosting services
    logging.info(f"Flask server attempting to start on port: {port}")
    try:
        # Use debug=False for production deployment
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logging.error(f"Failed to start Flask server: {e}")

# Function to start the web server thread
def keep_alive():
    """Starts the Flask server thread to keep the host alive."""
    t = Thread(target=run)
    t.start()
