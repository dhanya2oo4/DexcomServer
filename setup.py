from setuptools import setup, find_packages

setup(
    name="DexcomData",
    version="0.1.0",
    author="Dhanya",
    author_email="sridhanya3000@gmail.com",
    description="A Python library for monitoring continuous glucose data from the official Dexcom server",
    long_description="A Python library for monitoring continuous glucose data from the official Dexcom server",
    long_description_content_type="text/plain",
    url="https://github.com/yourusername/dexcom-glucose-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "web": [
            "flask>=2.0.0",
        ],
    },
)