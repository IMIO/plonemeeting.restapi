# -*- coding: utf-8 -*-
"""Installer for the plonemeeting.restapi package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [open("README.rst").read(), open("CHANGES.rst").read(), ])


setup(
    name="plonemeeting.restapi",
    version="1.0rc12",
    description="Extended rest api service for Products.PloneMeeting usecases",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone",
    author="Gauthier Bastien",
    author_email="gauthier@imio.be",
    url="https://pypi.python.org/pypi/plonemeeting.restapi",
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["plonemeeting"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        "setuptools",
        "Products.PloneMeeting",
        "imio.restapi>=1.0a12",
    ],
    extras_require={
        "test": ["plone.restapi[test]",
                 "Products.PloneMeeting[test]",
                 ], },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = plonemeeting.restapi.locales.update:update_locale
    """,
)
