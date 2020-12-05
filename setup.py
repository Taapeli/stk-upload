from setuptools import setup, find_packages

#See: https://setuptools.readthedocs.io/en/latest/setuptools.html

setup (
       name='stk_server',
       version='0.5',
       packages=find_packages(),

       # Declare your packages' dependencies here, for eg:
       install_requires=['flask', 'werkzeug', 'neo4j-driver', 'flask-security'],

       # Fill in these to make your Egg ready for upload to PyPI
       author='jm',
       author_email='juha.makelainen@iki.fi',

       description = 'Server program for Suomitietokanta',
       url='https://github.com/Taapeli/stk-upload',
       license='',
       long_description='Isotammi-palvelinsovellus',

       # could also include long_description, download_url, classifiers, etc.

       )
