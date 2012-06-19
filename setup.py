try:
    from setuptools import setup
    setup  # quiet "redefinition of unused ..." warning from pyflakes
    # arguments that distutils doesn't understand
    setuptools_kwargs = dict(
        extras_require={
            # add dependecies for mr3po modules here
            #
            #'quipu': ['python-inca', 'knottedcord>=0.3']
        },
        provides=['mr3po'],
        test_suite='tests.suite.load_tests',
        tests_require=['unittest2'],
    )
except ImportError:
    from distutils.core import setup

import mr3po

setup(
    author='David Marin',
    author_email='dave@yelp.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
    ],
    description=mr3po.__doc__,
    license='Apache',
    long_description=open('README.rst').read(),
    name='mr3po',
    packages=['mr3po'],
    url='http://github.com/Yelp/mr3po',
    version=mr3po.__version__,
    **setuptools_kwargs
)
