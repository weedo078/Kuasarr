# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

import setuptools

from kuasarr.providers.version import get_version

try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except:
    import io

    long_description = io.open('README.md', encoding='utf-8').read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="kuasarr",
    version=get_version(),
    author="weedo078",
    author_email="weedo0780@protonmail.com",
    description="kuasarr connects JDownloader with Radarr, Sonarr and LazyLibrarian. It also decrypts links protected by CAPTCHAs, using an additional CaptchaSolverr.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rix1337/Kuasarr",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={
        "kuasarr": [
            "static/*.png",
        ]
    },
    install_requires=required,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'kuasarr = kuasarr:run',
        ],
    },
)


