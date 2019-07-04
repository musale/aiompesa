from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="aiompesa",
    version="0.0.4",
    description="A package for accessing the MPESA daraja API from asyncio.",
    url="http://github.com/musale/aiompesa",
    author="Martin Musale",
    author_email="martinmshale@gmail.com",
    license="MIT",
    zip_safe=False,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
