#!/usr/bin/env python3
"""
Setup script for atoms-mcp package with CLI entry points
"""

from setuptools import find_packages, setup

# Define requirements manually
requirements = [
    "fastmcp>=2.13.0.1",
    "py-key-value-aio>=0.2.0",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "supabase>=2.5.0",
    "psycopg2-binary>=2.9.9",
    "google-cloud-aiplatform>=1.49.0",
    "aiohttp>=3.8.0",
    "workos>=1.0.0",
    "PyJWT>=2.8.0",
    "cryptography>=41.0.0",
    "tqdm>=4.66.0",
    "rapidfuzz>=3.10.0",
    "pydantic[email]>=2.11.7,<3.0.0",
    "pydantic-settings>=2.3.0",
    "httpx>=0.28.1,<1.0.0",
    "PyYAML>=6.0",
    "psutil>=5.9.0",
    "typing-extensions>=4.12.2",
    "playwright>=1.40.0",
    "sqlalchemy>=2.0.44",
    "rich>=13.0.0",
    "typer>=0.9.0",
]

# Setup package
setup(
    name="atoms-mcp",
    version="0.1.0",
    description="Atoms MCP Server - Model Context Protocol server for Atoms workspace management",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "atoms=atoms_cli:main_async",
        ],
    },
    python_requires=">=3.11",
    author="Atoms Team",
    author_email="",
    url="",
    license="MIT",
    long_description="Atoms MCP Server - Model Context Protocol server for Atoms workspace management",
    long_description_content_type="text/plain",
    include_package_data=True,
    zip_safe=False,
)
