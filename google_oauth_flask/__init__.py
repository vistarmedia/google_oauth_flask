import sys
from urlparse import urljoin

from functools import wraps

from flask import abort
from flask import redirect
from flask import request
from flask import session
from requests_oauthlib import OAuth2Session


from flask import current_app

_auth_state_key = 'oauth_state'
_oauth_route    = '/_oauth2/authorize'
user_info_url   = 'https://www.googleapis.com/oauth2/v1/userinfo'


def set_oauth_redirect_endpoint(app):
  '''
  takes a flask app and defines an endpoint for the oauth service to request to
  '''
  @app.route(_oauth_route)
  @oauth_redirect_endpoint(app.config)
  def _oauth2_authorize(user_details):
    '''
    - if authenticated, redirects them to the `dest_url` set in their session
    - if `dest_url` doesn't exist, redirect to '/'
    '''
    return redirect(session.get('dest_url') or '/')


def oauth_redirect(config=None):
  '''
  set the anti-forgery 'state' token in the session, return a redirect to the
  oauth url
  '''
  config        = config or current_app.config
  params        = _oauth_request_params(request, config)
  client_id     = config['GOOGLE_CONSUMER_KEY']
  oauth_url     = config['OAUTH_URL']
  oauth_session = OAuth2Session(client_id, **params)

  authorization_url, state = oauth_session.authorization_url(oauth_url)
  session[_auth_state_key] = state
  return redirect(authorization_url)


def oauth_user_token(config=None):
  '''
  return an oauth token for the user - expects the request it gets back from the
  oauth provider to have a "code" parameter and a `state` parameter
  if the state from the params (`stated_state`) doesn't match the `oauth_state`
  (`known_state`) stored in the session, we'll 403 af outta here

  abort with a 403 if anything goes wrong when fetching the token from the oauth
  provider
  '''
  config          = config or current_app.config
  known_state     = session.get(_auth_state_key)
  stated_state    = request.args.get('state')

  if not known_state or not stated_state or stated_state != known_state:
    # the requests_oauthlib library won't handle this check for us unless
    # we provide the known_state to the OAuth2Session constructor *and* use the
    # authorization_response kwarg (which is a url string) with `fetch_token`
    # we're not doing that since authorization_response must have https scheme
    abort(403)

  client_id       = config['GOOGLE_CONSUMER_KEY']
  client_secret   = config['GOOGLE_CONSUMER_SECRET']
  oauth_token_url = config['OAUTH_TOKEN_URL']
  redirect_url    = _redirect_url(request, config.get('OAUTH_REDIRECT_PATH'))

  code            = request.args.get('code')

  oauth_session   = OAuth2Session(client_id,
                                  state=known_state,
                                  redirect_uri=redirect_url)
  try:
    token = oauth_session.fetch_token(oauth_token_url,
                                      client_secret=client_secret,
                                      code=code)

  except Exception as e:
    raise e
    sys.stderr.write(e.message)
    abort(403)

  return token


def oauth_user_details(token, config=None):
  '''
  takes an oauth token and a config object and returns an object of user details
  '''
  config        = config or current_app.config
  client_id     = config['GOOGLE_CONSUMER_KEY']
  oauth_session = OAuth2Session(client_id, token=token)

  return oauth_session.get(user_info_url).json()


def oauth_redirect_endpoint(config=None):
  '''
  decorator to wrap the view function that responds to oauth provider response
  - sets session['oauth_email'] and session['oauth_token']
  - gives a user_details object as a kwarg to the wrapped view function
  '''
  config          = config or current_app.config
  allowed_domains = config.get('OAUTH_ALLOWED_DOMAINS')

  def decorator(view_func):
    @wraps(view_func)
    def view_wrapper(*args, **kwargs):
      token        = oauth_user_token(config)
      user_details = oauth_user_details(token, config)
      if not email_is_allowed(user_details.get('email'), allowed_domains):
        abort(403)
      session['oauth_email'] = user_details['email']
      session['oauth_token'] = token
      kwargs['user_details'] = user_details
      return view_func(*args, **kwargs)
    return view_wrapper
  return decorator


def is_authenticated():
  return session.get('oauth_email') and session.get('oauth_token')


def email_is_allowed(email, allowed_domains):
  '''
  if allowed_domains is empty, or not set allow logins from all domains
  otherwise match only listed domains
  '''
  return not allowed_domains or \
    any(email.endswith(d) for d in allowed_domains)


def _oauth_request_params(request, config):
  return {
    'redirect_uri':   _redirect_url(request, config.get('OAUTH_REDIRECT_PATH')),
    'scope':          ['email'],
  }


def _redirect_url(request, path):
  redir_path = path or _oauth_route
  return urljoin(request.url_root, redir_path)


def login_required(view):
  @wraps(view)
  def view_wrapper(*args, **kwargs):
    config = current_app.config
    if is_authenticated():
      return view(*args, **kwargs)
    else:
      session['dest_url'] = request.url
      return oauth_redirect(config)
  return view_wrapper
