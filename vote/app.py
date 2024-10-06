from flask import Flask, render_template, request, make_response, g # type: ignore
from redis import Redis, RedisError # type: ignore
import os
import socket
import random
import json
import logging

# Set default options from environment variables
option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

# Set up logging to include Gunicorn error logs
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    """Establish a Redis connection or reuse an existing one."""
    if not hasattr(g, 'redis'):
        try:
            g.redis = Redis(host="redis", db=0, socket_timeout=5)
        except RedisError as e:
            app.logger.error(f"Redis connection failed: {e}")
            g.redis = None
    return g.redis

@app.route("/", methods=['POST', 'GET'])
def hello():
    """Main route to handle voting."""
    # Retrieve or create a voter ID
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None
    redis = get_redis()

    if request.method == 'POST' and redis:
        try:
            vote = request.form['vote']
            app.logger.info(f"Received vote for {vote}")
            data = json.dumps({'voter_id': voter_id, 'vote': vote})
            redis.rpush('votes', data)
        except RedisError as e:
            app.logger.error(f"Error saving vote: {e}")

    # Render the index page with voting options and cookie management
    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

if __name__ == "__main__":
    # Run the application on all interfaces at port 80
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
