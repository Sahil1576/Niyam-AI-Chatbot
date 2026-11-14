from setuptools import setup, find_packages

REPO_NAME = "Niyam-AI-Chatbot"

PROJECT_NAME = "RBI_Guidelines_RAG"
AUTHOR = "Sahil1576"
AUTHOR_EMAIL = "sahilkatve7@gmail.com"
__version__ = "0.0.0"
SRC_REPO = "app"

setup(
    name=PROJECT_NAME,
    version=__version__,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=f"https://github.com/{AUTHOR}/{REPO_NAME}",
    description="RBI guidelines RAG Chatbot that answer the question from the RBI guidelines PDF.",
    packages=find_packages(where=SRC_REPO)
)