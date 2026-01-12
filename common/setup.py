from setuptools import setup, find_packages

setup(
    name="common",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Database
        "SQLAlchemy>=2.0.30,<3.0.0",
        "asyncpg>=0.29.0,<1.0.0",
        "psycopg2-binary>=2.9,<3.0",

        # Message queue
        "redis",

        # Provider SDKs
        "azure-storage-blob>=12.0.0",
        "openai",
        "requests>=2.28.0",

        # Retry logic
        "tenacity>=8.0.0",
    ],
)
