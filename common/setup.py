from setuptools import setup, find_packages

setup(
    name="common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "SQLAlchemy>=1.4",
        "asyncpg",
        "tenacity>=8.0.0",
        "openai",
        "requests>=2.28.0",
    ],
)
