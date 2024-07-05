from setuptools import setup, find_packages

setup(
    name="DocTemplify",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
    ],
    author="Damian Szumski",
    author_email="ds.damianszumski@gmail.com",
    description="A library for generating documents using Google Docs templates",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/DamianS21/DocTemplify",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)