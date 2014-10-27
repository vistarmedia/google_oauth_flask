# google_oauth_flask

[![Build Status](https://travis-ci.org/vistarmedia/google_oauth_flask.svg)](https://travis-ci.org/vistarmedia/google_oauth_flask)

The idea here is that you've got a buncha little flask apps you'd like like to
restrict access to, perhaps by the domain name of a user's email address.

### requirements

* flask app
* secure session
* having set up a "project" with oauth credentials and a name (under
  'credentials') at https://console.developers.google.com

### example app

```python

import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from flask import Flask

from google_oauth_flask import set_oauth_redirect_endpoint
from google_oauth_flask import login_required


app = Flask(__name__)
app.debug = True

app.config.update(
  SECRET_KEY             = 'supersecret',
  GOOGLE_CONSUMER_KEY    = 'yourkey-apps.googleusercontent.com',
  GOOGLE_CONSUMER_SECRET = 'your-secret',
  OAUTH_URL              = 'https://accounts.google.com/o/oauth2/auth',
  OAUTH_TOKEN_URL        = 'https://accounts.google.com/o/oauth2/token',
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

```

The `set_oauth_redirect_endpoint` takes your flask app instance and defines a
view function for `/_oauth2/authorize` that will redirect to the url the url was
trying to access before they logged in.

The `login_required` decorator should be used on any view function you'd like to
restrict access to.
