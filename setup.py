import setuptools

with open("Readme.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="celo-sdk",
    version="0.0.1",
    author="BlaizeTech",
    author_email="info@blaize.tech",
    description="Celo Python SDK to work with smart contracts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=required,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.8",

    ],
    python_requires='>=3.8',
)