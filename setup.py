from setuptools import setup

setup(
  name      = 'google-oauth-flask',
  description = 'A super simple flask decorator for oauth\'ing w/Google.',
  version   = '0.0.1',
  url       = 'https://github.com/vistarmedia/google_oauth_flask',
  packages  = ['google_oauth_flask'],

  install_requires = [
    'Flask             == 0.10.1',
    'requests_oauthlib == 0.4.2',
  ],

  test_suite = 'nose.collector',

  tests_require = [
    'Flask-Testing == 0.4.2',
    'httmock       == 1.2.2',
    'nose          == 1.3.4',
  ]
)
