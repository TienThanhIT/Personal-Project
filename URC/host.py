from flask import Flask
from threading import Thread

# Create the Flask app instance
app = Flask(__name__)

# Define the root route (this is what the host pings)
@app.route('/')
def home():
    # Return a simple status message
    return "Bot is awake and running!"

# Function to run the Flask server in a separate thread
def run():
    # host='0.0.0.0' is required for cloud hosting services to bind correctly
    # port=8080 is a common port, though hosts usually specify their own
    app.run(host='0.0.0.0', port=8080)

# Function to start the web server thread
def keep_alive():
    """Starts the Flask server thread to keep the host alive."""
    t = Thread(target=run)
    t.start()
