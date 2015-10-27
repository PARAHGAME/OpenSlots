#!/usr/bin/env python3

"""OpenSlots - Open-source framework for slot machine game development"""


from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='openslots',
    version='0.0.1-1',
    url='https://github.com/kopachris/OpenSlots',
    license='GPLv2',
    author='Christopher Koch',
    author_email='ch_koch@outlook.com',
    description='Open-source framework for slot machine game development',
    long_description=read('README.rst'),
    packages=['openslots'],
    scripts=[],
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',

        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',

        'Topic :: Games/Entertainment',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)