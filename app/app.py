import flask
import socket
import os

from app_logging import logger
import oauth_flow
import google_resources
from flask_sock import Sock
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = flask.Flask(__name__)
sock = Sock(app)

SCHEMA_HOST = "http://localhost"

@app.route("/")
def index():
    return flask.render_template('home.html')

@sock.route('/echo')
def echo(sock):
    while True:
        data = sock.receive()

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=data,
            temperature=0.6,
        )

        sock.send(data)

@app.route("/list_ip")
def list_ip():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        return flask.render_template('index.html', host_name, host_ip)
    except:
        return flask.render_template('error.html')

@app.route("/list_subscriptions")
def list_subscriptions():
    # check whether there is saved oauth refresh token; if not, redirect for login
    auth_url, state = oauth_flow.get_oauth_redirect_url('{0}/oauth2_authorize'.format(SCHEMA_HOST))
    logger.info('OAuth redirect URL: %s', auth_url)
    return flask.redirect(auth_url)


@app.route("/oauth2_authorize")
def oauth2_authorize():
    logger.debug('enter oauth2_authorize')

    # Check if there is an error
    oauth_error = flask.request.args.get('error')
    if oauth_error and len(oauth_error) > 0:
        logger.error('OAuth authorization failed: %s', oauth_error)
        return flask.render_template('error.html')

    oauth2_credentials = oauth_flow.fetch_access_refresh_token(
        authorization_url=flask.request.url,
        flask_session_state=flask.session['state'],
        call_back_url=flask.url_for('oauth2callback', _external=True)
    )
    logger.debug('get oauth2_credentials')

    # Store the credentials in the session.
    flask.session['credentials'] = {
        'token': oauth2_credentials.token,
        'refresh_token': oauth2_credentials.refresh_token,
        'token_uri': oauth2_credentials.token_uri,
        'client_id': oauth2_credentials.client_id,
        'client_secret': oauth2_credentials.client_secret,
        'scopes': oauth2_credentials.scopes
    }

    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.

    # request user id
    uid, email = google_resources.get_user_email(oauth2_credentials)

    return

@app.route("/oauth2callback")
def oauth2_callback():
    logger.info('oauth2callback is called: %s', flask.request.url)
    return 'success'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
