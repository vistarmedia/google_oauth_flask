from google_oauth_flask import login_required
from google_oauth_flask import set_oauth_redirect_endpoint

from test import authorize_route_installed
from test import successful_token_and_user_info_responses
from test import successful_token_response
from test import successful_user_info_response
from test import ViewTestCase


class TestGoogleOauthFlask(ViewTestCase):

  def setUp(self):
    @self.app.route('/restricted', methods=['GET'])
    @login_required
    def restricted():
      return 'SECRET EATING.'

  def test_oauth_redirect_response_unauthenticated(self):
    '''
    it should redirect user to the OAUTH_URL if they attempt to hit a
    @login_required resource when not authenticated
    '''
    resp = self.client.get('/restricted')
    self.assertRedirectsTo('https://accounts.example.com/o/oauth2/auth', resp)

  def test_restricted_resource_allowed_for_authenticated_user(self):
    self.as_authenticated_user()
    resp = self.client.get('/restricted')
    self.assert200(resp)
    self.assertEquals('SECRET EATING.', resp.data)

  def test_oauth_redirect_response_unauthenticated_with_destination(self):
    '''
    it should set a `dest_url` in the user's session which will match the
    resource they attempted to access while unauthenticated
    '''
    resp = self.client.get('/restricted')
    session = self.get_session(resp)
    self.assertIsNotNone(session['dest_url'])
    self.assertEqual('http://localhost/restricted', session['dest_url'])

  def test_oauth_redirect_response_sets_oauth_state_in_session(self):
    '''
    it should set an oauth_state value in session to be used for forgery
    protection
    '''
    resp    = self.client.get('/restricted')
    session = self.get_session(resp)
    self.assertIsNotNone(session.get('oauth_state'))

  def test_set_oauth_redirect_endpoint(self):
    '''
    it should add an /_oauth2/authorize endpoint route to the app
    '''
    self.assertFalse(self.app.view_functions.get('_oauth2_authorize'))
    set_oauth_redirect_endpoint(self.app)
    self.assertTrue(self.app.view_functions.get('_oauth2_authorize'))

  def test_set_oauth_redirect_endpoint_with_authentication(self):
    '''
    it should redirect from the defined endpoint to the resource the user was
    initially trying to access - set in session at `dest_url`
    '''
    auth_route = authorize_route_installed(self.app)
    with auth_route, successful_token_and_user_info_responses():
      self.set_session({
        'dest_url': 'http://pods.example.com/',
        'oauth_state': 'honk'
      })
      resp = self.client.get('/_oauth2/authorize?code=honk&state=honk')
      self.assertRedirectsTo('http://pods.example.com/', resp)

  def test_define_endpoint_redirect_after_authentication_no_dest_url(self):
    '''
    it should redirect to / if a authenticated user's session is missing a
    `dest_url`
    '''
    auth_route = authorize_route_installed(self.app)
    with auth_route, successful_token_and_user_info_responses():
      self.set_session({
        'oauth_state': 'honk',
      })
      resp = self.client.get('/_oauth2/authorize?code=honk&state=honk')
      self.assertRedirectsTo('http://localhost/', resp)

  def test_oauth_redirect_endpoint_rejects_emails_that_dont_match_domains(self):
    '''
    it should 403 if user authentication succeeds but email address is not in
    allowed domains list
    '''
    auth_route = authorize_route_installed(self.app)
    info = {
      'email': 'dudley.perkins@stonesthrow.com'
    }
    with auth_route, successful_token_response(),\
      successful_user_info_response(info):
      self.set_session({'oauth_state': 'honk'})
      resp = self.client.get('/_oauth2/authorize?code=honk&state=honk')
      self.assert403(resp)

  def test_oauth_endpoint_mismatched_state(self):
    '''
    it should 403 if state in GET request doesn't match state in session
    '''
    auth_route = authorize_route_installed(self.app)
    with auth_route, successful_token_and_user_info_responses():
      self.set_session({'oauth_state': 'feebs'})
      resp = self.client.get('/_oauth2/authorize?code=honk&state=honk')
      self.assert403(resp)

  def test_oauth_endpoint_matched_state(self):
    '''
    it should not 403 if token and user info success and state matches
    '''
    with successful_token_and_user_info_responses():
      self.set_session({'oauth_state': 'honk'})
      resp = self.client.get('/authorized?code=honk&state=honk')
      self.assertNotEqual(403, resp.status_code)
