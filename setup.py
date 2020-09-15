import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="nokia1830pss",
    version="1.0.3",
    author="Trung Truong",
    author_email="trungdtbk@gmail.com",
    description="A SSH library for Nokia 1830-PSS NEs",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/trungdtbk/nokia-1830pss-ssh.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Networking"
    ],
    install_requires=[
        'paramiko==2.7.0'
    ]
)