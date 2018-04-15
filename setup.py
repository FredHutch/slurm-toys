from setuptools import setup

__version__ = "0.1"

#try:
#    from pypandoc import convert
#    read_md = lambda f: convert(f, 'rst')
#except ImportError:
#    print("warning: pypandoc module not found, could not convert Markdown to RST")
#    read_md = lambda f: open(f, 'r').read()

CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Customer Service",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Information Technology",
    "Intended Audience :: Science/Research",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: Apache Software License",
    "Natural Language :: English",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Unix Shell",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Systems Administration",
    "Topic :: Utilities"
]

setup(
    name='slurm-toys',
    version=__version__,
    description='helper tools for the SLURM HPC workload manager used at Fred Hutch and elsewhere',
    long_description=open('README.rst', 'r').read(),
    packages=['slurm_toys'],
    #scripts=['bin/slurm-toys'],
    author = 'dipe',
    author_email = 'dp@nowhere.com',
    url = 'https://github.com/FredHutch/slurm-toys',
    download_url = 'https://github.com/FredHutch/slurm-toys/tarball/%s' % __version__,
    keywords = ['slurm', 'hpc', 'scientific computing'], # arbitrary keywords
    classifiers = CLASSIFIERS,
    install_requires=[
        'pandas',
        'requests',
        'python-hostlist',
        ],
    entry_points={
        # we use console_scripts here to allow virtualenv to rewrite shebangs
        # to point to appropriate python and allow experimental python 2.X
        # support.
        'console_scripts': [
            'slurm-limiter=slurm_toys.slurm-limiter:main',
        ]
    }
)
