from flask import Flask
from threading import Thread
import os # <-- REQUIRED to read the PORT environment variable

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
    # 2. Use the standard fallback of 8080 if 'PORT' is not set (e.g., when running locally)
    port = int(os.environ.get("PORT", 8080))
    
    # host='0.0.0.0' is required for cloud hosting services to bind correctly
    print(f"Flask server attempting to start on port: {port}")
    app.run(host='0.0.0.0', port=port)

# Function to start the web server thread
def keep_alive():
    """Starts the Flask server thread to keep the host alive."""
    t = Thread(target=run)
    t.start()
