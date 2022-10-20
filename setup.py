# -*- coding: UTF-8 -*-
#
#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

#See: https://setuptools.readthedocs.io/en/latest/setuptools.html

setup (
       name='stk_server',
       version='2022.1',
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
