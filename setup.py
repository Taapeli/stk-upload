from setuptools import setup, find_packages

setup (
       name='stk_server',
       version='0.1',
       packages=find_packages(),

       # Declare your packages' dependencies here, for eg:
       install_requires=['flask', 'werkzeug', 'neo4j-driver', 'flask-security'],

       # Fill in these to make your Egg ready for upload to
       # PyPI
       author='jm',
       author_email='juha.makelainen@iki.fi',

       summary = 'Server program for Suomitietokanta',
       url='',
       license='',
       long_description='Taapeli-palvelinsovellus',

       # could also include long_description, download_url, classifiers, etc.

       )
