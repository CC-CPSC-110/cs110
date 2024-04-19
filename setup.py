from setuptools import setup

from cs110 import __version__

setup(
    name='cs110',
    version=__version__,

    url='https://github.com/CC-CPSC-110/cs110',
    author='Paul Bucci',
    author_email='paul.bucci@ubc.ca',
    install_requires=[
        'mypy',
        'pylint'
    ],
    py_modules=['cs110'],
)
