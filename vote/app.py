from flask import Flask, render_template, request, make_response, g
from redis import Redis, RedisError
import os
import socket
import random
import json
import logging

# Environment variables for the vote options
option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

# Setup logging using gunicorn's error logger if available
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    """Function to get Redis connection and handle exceptions."""
    if not hasattr(g, 'redis'):
        try:
            g.redis = Redis(host="redis", db=0, socket_timeout=5)
        except RedisError as e:
            app.logger.error("Failed to connect to Redis: %s", e)
            g.redis = None
    return g.redis

@app.route("/", methods=['POST', 'GET'])
def hello():
    """Main voting route to handle votes and display the voting page."""
    voter_id = request.cookies.get('voter_id')
    
    # Generate a new voter_id if one does not exist
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None
    redis = get_redis()

    # Handle POST request when user submits a vote
    if request.method == 'POST':
        if redis:
            vote = request.form['vote']
            app.logger.info('Received vote for %s', vote)
            try:
                # Push vote data to Redis list
                data = json.dumps({'voter_id': voter_id, 'vote': vote})
                redis.rpush('votes', data)
            except RedisError as e:
                app.logger.error("Error while pushing to Redis: %s", e)
        else:
            app.logger.error('Cannot process vote, Redis unavailable.')

    # Prepare response and set the voter_id cookie
    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

# Main entry point for the application
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
