import setuptools


with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="",
    version="1.5.8",
    keywords="",
    author="",
    author_email="",
    description="",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="GPLv3",
    url="https://qfluentwidgets.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "PyQt5-Frameless-Window>=0.3.3",
        "darkdetect",
    ],
    extras_require = {
        'full': ['scipy', 'pillow', 'colorthief']
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent'
    ],
    project_urls={
        'Documentation': '',
        'Source Code': '',
        'Bug Tracker': '',
    }
)
