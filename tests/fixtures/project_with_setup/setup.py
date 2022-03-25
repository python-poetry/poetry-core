from setuptools import setup


kwargs = dict(
    name="my-package",
    license="MIT",
    version="0.1.2",
    description="Demo project.",
    author="Sébastien Eustace",
    author_email="sebastien@eustace.io",
    url="https://github.com/demo/demo",
    packages=["my_package"],
    install_requires=["pendulum>=1.4.4", "cachy[msgpack]>=0.2.0"],
)


setup(**kwargs)
