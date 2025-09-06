from setuptools import setup, find_packages

setup(
    name="financial_server",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=2.0.0",
        "yfinance>=0.1.63",
        "requests>=2.26.0",
        "python-dateutil>=2.8.2",
        "pytest>=6.2.5",
        "pytest-asyncio>=0.16.0",
        "httpx>=0.19.0"
    ],
    python_requires=">=3.8",
    author="Marcel",
    description="A local financial data server with real-time data fetching and caching",
    keywords="finance,data,server,api,bitcoin,stocks",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Programming Language :: Python :: 3",
    ],
)
