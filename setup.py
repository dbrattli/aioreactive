# read the contents of your README file
from os import path

from setuptools import find_packages, setup

import versioneer

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="aioreactive",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Async/await Reactive Tools for Python 3.9+",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Børge Lanes & Dag Brattli",
    author_email="dag@brattli.net",
    license="MIT License",
    url="https://github.com/dbrattli/aioreactive",
    download_url="https://github.com/dbrattli/aioreactive",
    zip_safe=True,
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=["expression"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-asyncio", "pytest-cov", "hypothesis"],
    package_data={"aioreactive": ["py.typed"]},
    packages=find_packages(),
    package_dir={"aioreactive": "aioreactive"},
)
