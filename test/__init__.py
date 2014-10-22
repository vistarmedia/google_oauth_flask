from contextlib import contextmanager
from json import dumps
from json import loads

from flask import Flask
from flask import request
from flask import session
from flask.ext.testing import TestCase
from flask.sessions import SessionInterface
from flask.sessions import SessionMixin
from werkzeug.http import parse_cookie

from httmock import urlmatch
from httmock import response
from httmock import HTTMock

from google_oauth_flask import set_oauth_redirect_endpoint


session_cookie_name = 'nbd'


class JSONSession(dict, SessionMixin):
  pass


class SessionInterfaceForTest(SessionInterface):
  '''
  simple flask session interface - just throw json in as cookie value for
  testing purposes
  '''

  session_class = JSONSession

  def open_session(self, app, request):
    val = request.cookies.get(app.session_cookie_name)
    if val:
      return JSONSession(loads(val))
    else:
      return JSONSession()

  def save_session(self, app, session, response):
    response.set_cookie(app.session_cookie_name, dumps(session))


class ViewTestCase(TestCase):

  def create_app(self):
    self.app = Flask(__name__)
    self.app.session_interface = SessionInterfaceForTest()
    self.app.config.update(
      TESTING                = True,
      DEBUG                  = True,
      SESSION_COOKIE_NAME    = session_cookie_name,
      GOOGLE_CONSUMER_KEY    = 'g-consumer-key',
      GOOGLE_CONSUMER_SECRET = 'g-consumer-secret',
      OAUTH_URL              = 'https://accounts.example.com/o/oauth2/auth',
      OAUTH_TOKEN_URL        = 'https://accounts.example.com/o/oauth2/token',
      OAUTH_ALLOWED_DOMAINS  = ('example.com',)
    )

    @self.app.route('/_set_session', methods=['POST'])
    def _set_session():
      # make a dummy route and post to it, setting session values
      # clear the session if empty params are sent
      body = loads(request.data)
      if body:
        for key, val in body.iteritems():
          session[key] = val
      else:
        session.clear()
      return 'OKAY!'

    return self.app

  def assert302(self, resp):
    return self.assertEqual(302, resp.status_code)

  def assert403(self, resp):
    return self.assertEqual(403, resp.status_code)

  def assertRedirectsTo(self, location, resp):
    '''
    check that the value of the location header begins with given location
    '''
    regex = r"^%s" % location
    self.assert302(resp)
    self.assertRegexpMatches(resp.headers.get('Location'), regex)

  def get_session(self, resp):
    '''
    get the value of the Set-Cookie header, load the value as JSON since that's
    what we're working with for test purposes
    '''
    cookies = parse_cookie(resp.headers.get('Set-Cookie'))
    return loads(cookies.get(session_cookie_name))

  def set_session(self, params):
    self.client.post('/_set_session', data=dumps(params))

  def as_authenticated_user(self):
    params = {
      'oauth_email': 'j@example.com',
      'oauth_token': 't-t-t-t-t-token!'
    }
    self.set_session(params)


@contextmanager
def successful_token_response():
  @urlmatch(scheme='https', netloc='accounts.example.com',
            path='/o/oauth2/token')
  def token_content(url, request):
    headers = {
      'content-type': 'application/json'
    }
    content = {
      'access_token' : 'access-token',
      'token_type' : 'Bearer',
      'expires_in' : 3600,
      'id_token' : 'id-token'
    }
    return response(200, content, headers, request=request)

  with HTTMock(token_content):
    yield


@contextmanager
def successful_user_info_response(content={'email': 'j@example.com'}):
  @urlmatch(scheme='https', netloc='www.googleapis.com',
            path='/oauth2/v1/userinfo')
  def user_info_content(url, request):
    headers = {
      'content-type': 'application/json'
    }
    return response(200, content, headers, request=request)

  with HTTMock(user_info_content):
    yield


@contextmanager
def successful_token_and_user_info_responses():
  with successful_token_response(), successful_user_info_response():
    yield


@contextmanager
def failed_token_response():
  @urlmatch(scheme='https', netloc='accounts.example.com',
            path='/o/oauth2/token')
  def token_content(url, request):
    headers = {
      'content-type': 'application/json'
    }
    content = '''
    honk
    '''
    return response(400, content, headers, request=request)

  with HTTMock(token_content):
    yield


@contextmanager
def authorize_route_installed(app):
  set_oauth_redirect_endpoint(app)
  yield
