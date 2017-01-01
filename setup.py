from setuptools import setup, find_packages

# with open('README.rst') as fp:
#     README = fp.read()

setup(
    name='pyegs',
    version='0.1',
    author='Sviatoslav Abakumov',
    author_email='dust.harvesting@gmail.com',
    description='Compile subset of Python to Egiks in Quake 2 scenarios',
    # long_description=README,
    url='https://github.com/Perlence/pyegs',
    download_url='https://github.com/Perlence/pyegs/archive/master.zip',
    packages=find_packages('.'),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'pyegs = pyegs.cli:main',
        ],
    },
    install_requires=[
        'attrs',
        'funcy',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
    ]
)
