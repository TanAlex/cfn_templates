"""
AWS SAM Serverless Application Model
"""
import io
import os
import re

from setuptools import setup, find_packages


def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", os.linesep)
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def read_version():
    content = read(os.path.join(os.path.dirname(__file__), "samtranslator", "__init__.py"))
    return re.search(r"__version__ = \"([^']+)\"", content).group(1)


def read_requirements(req="base.txt"):
    content = read(os.path.join("requirements", req))
    return [line for line in content.split(os.linesep) if not line.strip().startswith("#")]


setup(
    name="aws-sam-translator",
    version=read_version(),
    description="AWS SAM Translator is a library that transform SAM templates into AWS CloudFormation templates",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Amazon Web Services",
    author_email="aws-sam-developers@amazon.com",
    url="https://github.com/awslabs/serverless-application-model",
    license="Apache License 2.0",
    # Exclude all but the code folders
    packages=find_packages(exclude=("tests", "docs", "examples", "versions")),
    install_requires=read_requirements("base.txt"),
    include_package_data=True,
    extras_require={"dev": read_requirements("dev.txt")},
    keywords="AWS SAM Serverless Application Model",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
    ],
)