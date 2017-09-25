#!/usr/bin/env python
import os
import setuptools

#with open('README.rst') as f:
#    readme = f.read()

#with open('LICENSE') as f:
#    license = f.read()

os.environ['STATICBUILD'] = 'true'
REQUERIMIENTOS = ['requests',
                  'BeautifulSoup4',
                  'lxml' # Requiere Visual C++ 2015 Build Tools (Falta revisar) y import os + os.environ['STATICBUILD'] = 'true'
                  ]

setuptools.setup(
    name='Challenge',
    version='0.1.dev0',
    #packages=['towelstuff',],
    license='GPLv3',
    url='http://github.com/leapalazzolo/Challenge',
    author='Leandro Palazzolo',
    author_email='leapalazzolo@gmail.com',
    #long_description=open('README.txt').read(),
    #packages=find_packages(exclude=('tests', 'docs')),
    install_requires=REQUERIMIENTOS,
    #test_requires=REQUERIMIENTOS
)
