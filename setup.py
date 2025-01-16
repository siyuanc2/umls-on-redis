from setuptools import setup, find_packages

setup(
    name='cptdb',
    version='0.1.0',
    author='Siyuan Chen',
    author_email='siyuanc2@illinois.edu',
    description='A package to interact with a Redis database containing CPT codes and their hierarchies.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/siyuanc2/umls-on-redis',
    packages=find_packages(),
    install_requires=[
        'redis',
        'owlready2',
        # Add other dependencies as needed
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
