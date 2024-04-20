from setuptools import setup, find_packages

setup(
    name='cs110',
    version='0.1',
    packages=find_packages(),
    package_data={
        "cs110": ["py.typed"],  # Include py.typed marker
    },
    description="Course tools for CS 110",
    long_description=open('README.md').read(),
    url='https://github.com/CC-CPSC-110/cs110',
    author='Paul Bucci',
    author_email='paul.bucci@ubc.ca',
    install_requires=open('requirements.txt').read().splitlines(),
    py_modules=['cs110'],
    zip_safe=False,  # This is important for mypy to find the py.typed file

)
