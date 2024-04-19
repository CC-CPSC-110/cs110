from setuptools import setup

from my_pip_package import __version__

setup(
    name='cs110',
    version=__version__,

    url='https://github.com/CC-CPSC-110/cs110',
    author='Paul Bucci',
    author_email='paul.bucci@ubc.ca',

    py_modules=['cs110'],
)
