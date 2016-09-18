"""
    adbpy
    ~~~~~

    Python implementation of the Android Debug Bridge (ADB).
"""

import ast
import re


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


version_regex = re.compile(r'__version__\s+=\s+(.*)')


def get_version():
    with open('adb/__init__.py', 'r') as f:
        return str(ast.literal_eval(version_regex.search(f.read()).group(1)))


setup(
    name='adbpy',
    version=get_version(),
    author='Andrew Hawker',
    author_email='andrew.r.hawker@gmail.com',
    url='https://github.com/ahawker/adbpy',
    license='Apache 2.0',
    description='Python implementation of the Android Debug Bridge (ADB).',
    long_description=__doc__,
    packages=['adb'],
    package_dir={'adb': 'adb'},
    include_package_data=True,
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3'
        'Programming Language :: Python :: 3.4'
        'Programming Language :: Python :: 3.5'
    )
)
