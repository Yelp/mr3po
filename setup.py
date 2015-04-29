import os

try:
    from setuptools import setup
    setup  # quiet "redefinition of unused ..." warning from pyflakes
    # arguments that distutils doesn't understand
    setuptools_kwargs = dict(
        extras_require={
            # add dependecies for mr3po modules here
            'yaml': ['PyYAML'],
        },
        provides=['mr3px'],
        test_suite='tests.suite.load_tests',
        tests_require=['mock', 'unittest2'],
    )
except ImportError:
    from distutils.core import setup


try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert MD to RST")
    read_md = lambda f: open(f, 'r').read()

import mr3px

setup(
    author='David Marin, Max Sharples',
    author_email='maxsharples@gmail.com',
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
    description=mr3px.__doc__,
    license='Apache',
    long_description=read_md(os.path.abspath(os.path.join(
                             os.path.dirname(__file__),
                             'README.md'))),
    name='mr3px',
    packages=['mr3px'],
    url='http://github.com/msharp/mr3po',
    version=mr3px.__version__,
    **setuptools_kwargs
)
