from setuptools import setup, find_packages
REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]
setup(
    name='UtilityLib',
    version='2.0',
    packages=find_packages(),
    description='UtilityLib v2',
    author='Vishal K Sahu',
    author_email='contact@thebiomics.com',
    url='https://www.thebiomics.com',
    install_requires=REQUIREMENTS,
)
