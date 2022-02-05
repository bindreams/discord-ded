from setuptools import setup, find_packages

install_requires = [
    "discord.py",
    "sortedcontainers",
    "flask",
    "PyYAML"
]

entry_points = {
    "console_scripts": ["discord-ded = discord_ded.__main__:main"],
}

setup(
    name="discord-ded",
    version="0.2.0",
    description="Discord lesson bot",
    author="Andrey Zhukov",
    author_email="andres.zhukov@gmail.com",
    license="MIT",
    install_requires=install_requires,
    packages=find_packages(),
    entry_points=entry_points
)
