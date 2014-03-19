#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(name='JumpScale Libs',
      version='6.0.0',
      description='Python Automation framework',
      author='JumpScale',
      author_email='info@jumpscale.org',
      url='http://www.jumpscale.org',

      packages=find_packages(),
      include_package_data=True,
      zip_safe = False,
      namespace_packages = ['JumpScale'],

      download_url='http://pypi.python.org/pypi/JumpScale/',
      install_requires=[],
      classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)

