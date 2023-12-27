from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open("README.md", "r") as fh:
    description = fh.read()

setup(
    name="fast_azure_client",
    version="1.1.1",
    description="This package helps ease integration between python (fastapi) applications and "
                "Microsoft Azure AD / AD B2C authentication flows",
    long_description=description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    license='MIT',
    entry_points={
        'console_scripts': [
            'fast_azure_client=fast_azure_client.main:main',
        ],
    },
)
