from setuptools import setup, find_packages

setup(
    name="db_core",
    version="0.1.0",
    packages=find_packages(include=["db_core", "db_core.*"]),
    install_requires=[
        "SQLAlchemy>=1.4",
        "asyncpg",            # or your async driver of choice
        # any other dependencies
    ],
)