try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name='aioreactive',
    version='0.2.1',
    description='Async/await Reactive Tools for Python 3.5+',
    long_description=(
        "aioreactive is a library for asynchronous and reactive "
        "programming using asyncio, async and await"),
    author='Børge Lanes & Dag Brattli',
    author_email='dag@brattli.net',
    license='MIT License',
    url='https://github.com/dbrattli/aioreactive',
    download_url='https://github.com/dbrattli/aioreactive',
    zip_safe=True,

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', "pytest-asyncio"],

    packages=['aioreactive', 'aioreactive.abc', 'aioreactive.core',
              'aioreactive.ops', 'aioreactive.testing',
              'aioreactive.producer', 'aioreactive.observable'],
    package_dir={'aioreactive': 'aioreactive'}
)
