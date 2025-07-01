from setuptools import setup, find_packages

setup(
    name="m3u8-codec-forward",
    version="0.1.0",
    description="M3U8 codec forwarding library for multiple stream variants",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "httpx>=0.23.3,<0.24.0",
        "m3u8>=3.5.0",
        "ffmpeg-python>=0.2.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-httpx>=0.21.2",
        ]
    },
    python_requires=">=3.8",
)