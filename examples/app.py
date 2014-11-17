import os
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from flask import Flask

from google_oauth_flask import set_oauth_redirect_endpoint
from google_oauth_flask import login_required


os.environ['DEBUG'] = 'true'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
app = Flask(__name__)
app.debug = True

app.config.update(
  SECRET_KEY             = 'supersecret',
  GOOGLE_CONSUMER_KEY    = 'yourkey-apps.googleusercontent.com',
  GOOGLE_CONSUMER_SECRET = 'your-secret',
  OAUTH_URL              = 'https://accounts.google.com/o/oauth2/auth',
  OAUTH_TOKEN_URL        = 'https://accounts.google.com/o/oauth2/token',
  OAUTH_USER_INFO_URL    = 'https://www.googleapis.com/oauth2/v1/userinfo',
  OAUTH_ALLOWED_DOMAINS  = ('vistarmedia.com',)
)

set_oauth_redirect_endpoint(app)


@app.route('/', methods=['GET'])
@login_required
def index():
  return '''
  <html>
    <head></head>
    <body>
      <div style='font-weight: 900; font-size: 36px; width: auto;'>
        TOTALLY SECRET
      </div>
    </body>
  </html>
  '''


@app.route('/restricted', methods=['GET'])
@login_required
def restricted():
  return '''
  <html>
    <head></head>
    <body>
      <div style='font-weight: 900; font-size: 36px; width: auto;'>
        hey, you tried to get here before.  now you're here
      </div>
    </body>
  </html>
  '''


if __name__ == "__main__":
  app.run(port=8888, host='0.0.0.0', use_debugger=True, debug=True,
      use_reloader=True)
