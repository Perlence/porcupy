from setuptools import setup, find_packages

# with open('README.rst') as fp:
#     README = fp.read()

setup(
    name='porcupy',
    version='0.1',
    author='Sviatoslav Abakumov',
    author_email='dust.harvesting@gmail.com',
    description='Compile a subset of Python to Egiks in Quake II scenarios',
    # long_description=README,
    url='https://github.com/Perlence/porcupy',
    download_url='https://github.com/Perlence/porcupy/archive/master.zip',
    packages=find_packages('.'),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'porcupy = porcupy.cli:main',
        ],
    },
    install_requires=[
        'attrs',
        'funcy',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Games/Entertainment',
        'Topic :: Games/Entertainment :: Side-Scrolling/Arcade Games',
        'Topic :: Software Development',
        'Topic :: Software Development :: Compilers',
        'Topic :: Utilities',
    ]
)
