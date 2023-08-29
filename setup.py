from setuptools import setup, find_packages
REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]
LONG_DESCRIPTION = "".join(open("readme.md").readlines())
setup(
    name='UtilityLib',
    version='2.6',
    packages=find_packages(),
    description='UtilityLib: Think, Explore, and Master',
    author='Vishal K Sahu',
    author_email='mail@vishalkumarsahu.in',
    url='https://github.com/TheBiomics/UtilityLib',
    install_requires=REQUIREMENTS,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
)
