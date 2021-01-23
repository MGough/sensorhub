import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sensorhub",
    version="2.0.2",
    author="Merlin Gough",
    author_email="goughmerlin@gmail.com",
    description="A simple library to use with the DockerPi SensorHub (EP-0106)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MGough/sensorhub",
    packages=["sensorhub"],
    install_requires=["smbus2>=0.3.0"],
    tests_require=["pytest>=5.4.3"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)