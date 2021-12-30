from setuptools import setup, find_packages

install_requires = [
    "discord.py",
    "sortedcontainers",
    "flask",
    "PyYAML"
]

setup(
    name="discord-ded",
    version="0.2.0",
    description="Discord lesson bot",
    author="Andrey Zhukov",
    author_email="andres.zhukov@gmail.com",
    license="MIT",
    install_requires=install_requires,
    packages=find_packages()
)
