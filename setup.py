#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import setuptools

with open('README.md') as f:
    leeme = f.read()

with open('LICENSE.md') as f:
    licencia = f.read()

with open('requirements.txt') as f:
    requerimientos = f.read()

os.environ['STATICBUILD'] = 'true'
#REQUERIMIENTOS = ['BeautifulSoup4',
#                  'lxml' # Requiere Visual C++ 2015 Build Tools (Falta revisar) y import os + os.environ['STATICBUILD'] = 'true'
#                  ]

setuptools.setup(
    name='XSS',
    version='1.0',
    description='Detector de vulnerabilidaes XSS',
    long_description=leeme,
    url='http://github.com/leapalazzolo/XSS',
    author='Leandro Palazzolo',
    author_email='leapalazzolo@gmail.com',
    license=licencia,
    install_requires=requerimientos,
)
