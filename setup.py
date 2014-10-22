from setuptools import setup

setup(
  name      = 'google_oauth_flask',
  version   = '0.0.1',
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
