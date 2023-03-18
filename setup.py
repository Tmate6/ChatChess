import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chatchess",
    version="1.1.2",
    author="Mate Tohai",
    author_email="admin@tmate6.com",
    description="A package to play chess with ChatGPT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tmate6/ChatChess",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "chess",
        "openai",
    ],
)