from setuptools import setup, find_packages

setup(
    name="providers",
    version="0.1.0",
    packages=find_packages(include=["providers", "providers.*"]),
    install_requires=[
        "openai",
        "requests>=2.28.0",
        "tenacity>=8.0.0",    # Retry logic for API calls
        "azure-storage-blob>=12.8.0",
    ],
)
