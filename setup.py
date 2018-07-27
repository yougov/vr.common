#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import setuptools

name = 'vr.common'
description = 'Libraries and for deploying with Velociraptor'
nspkg_technique = 'managed'
"""
Does this package use "native" namespace packages or
pkg_resources "managed" namespace packages?
"""

params = dict(
    name=name,
    use_scm_version=True,
    author="Brent Tubbs",
    author_email="brent.tubbs@gmail.com",
    description=description or name,
    url="https://github.com/yougov/" + name,
    packages=setuptools.find_packages(),
    include_package_data=True,
    namespace_packages=(
        name.split('.')[:-1] if nspkg_technique == 'managed'
        else []
    ),
    python_requires='>=2.7',
    install_requires=[
        'six>=1.4.1',
        'utc',
        'requests',
        'PyYAML>=3.10',
        'sseclient==0.0.11',
        'contextlib2',
    ],
    extras_require={
        'testing': [
            # upstream
            'pytest>=3.5',
            'pytest-sugar>=0.9.1',
            'collective.checkdocs',
            'pytest-flake8',

            # local
            'redis',
            'pytest-redis',
        ],
        'docs': [
            # upstream
            'sphinx',
            'jaraco.packaging>=3.2',
            'rst.linker>=1.9',

            # local
        ],
        ':python_version=="2.7"': [
            'suds==0.4',
        ],
        ':python_version!="2.7"': [
            'suds-py3',
        ],

        'balancers': [
            'paramiko',
        ],
        'balancers:python_version=="2.7"': [
            'django<2',
        ],
        'balancers:python_version!="2.7"': [
            'django',
        ],
    },
    setup_requires=[
        'setuptools_scm>=1.15.0',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ],
    entry_points={
    },
)
if __name__ == '__main__':
    setuptools.setup(**params)
