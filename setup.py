from setuptools import setup, find_packages

setup(
    name="wiki_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
        "requests>=2.31.0",
        "markdown>=3.5.1",
        "beautifulsoup4>=4.12.0",
        "python-docx>=0.8.11",
        "chromadb>=0.4.0,<0.5.0",
        "numpy>=1.20.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.4.3",
        "python-multipart>=0.0.6",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="一个用于从不同数据源获取内容的Python工具",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
)