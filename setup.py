from setuptools import setup, find_packages

setup(
    name='arboretum',
    version='0.0.1',
    packages=find_packages(),
    url='https://github.com/JLane-scripps/Arboretum.git',
    license='MIT',
    author='Jeff Lane, Patrick Garrett',
    author_email='jlane@scripps.edu, pgarrett@scripps.edu',
    description='Several data storage trees and a handler class, for mass-spec PSM storage & searching',
    install_requires=[
        'numpy~=1.23.1',
        'sortedcontainers',
        'intervaltree~=3.1.0',
        'ranged-bintrees @ git+https://github.com/pgarrett-scripps/ranged_bintrees.git',
        'ranged-kdtree @ git+https://github.com/pgarrett-scripps/ranged_kdtree.git',
    ],
    extras_require={
        'benchmark': ['matplotlib~=3.5.2'],
    },
)
