from flask import Flask, render_template, request, make_response, g
import boto3
import os
import socket
import random
import json
import logging

# Get environment variables for voting options
option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

# Set up logging to integrate with Gunicorn
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

# Initialize the SNS client
sns_client = boto3.client('sns')
topic_arn = json.loads(os.getenv('COPILOT_SNS_TOPIC_ARNS'))['votes']

@app.route("/", methods=['POST', 'GET'])
def hello():
    # Retrieve or generate a voter ID
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        vote = request.form['vote']
        app.logger.info('Received vote for %s', vote)

        # Prepare the message to publish to SNS
        data = {
            'voter_id': voter_id,
            'vote': vote,
        }
        try:
            sns_client.publish(
                TargetArn=topic_arn,
                Message=json.dumps({'default': json.dumps(data)}),
                MessageStructure='json'
            )
            app.logger.info('Vote published to SNS: %s', data)
        except Exception as e:
            app.logger.error('Failed to publish vote to SNS: %s', str(e))

    # Render the response
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
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
