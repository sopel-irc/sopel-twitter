# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
from setuptools import setup, find_packages


if __name__ == '__main__':
    print('Sopel does not correctly load modules installed with setup.py '
          'directly. Please use "pip install .", or add {}/sopel_modules to '
          'core.extra in your config.'.format(
              os.path.dirname(os.path.abspath(__file__))),
          file=sys.stderr)

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('NEWS') as history_file:
    history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = [req for req in requirements_file.readlines()]


setup(
    name='sopel_modules.twitter',
    version='1.0.1',
    description='A Twitter plugin for Sopel',
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    author='dgw',
    author_email='dgw@technobabbl.es',
    url='https://github.com/sopel-irc/sopel-twitter',
    packages=find_packages('.'),
    namespace_packages=['sopel_modules'],
    include_package_data=True,
    install_requires=requirements,
    license='Eiffel Forum License, version 2',
)
