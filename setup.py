import codecs
import os
import re
import setuptools


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")



setuptools.setup(
    name='whim',
    version=find_version('src', 'whim', '__init__.py'),
    description='A simple editor',
    license='gpl-3.0',
    url='https://github.com/Sibilance/whim',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Collin RM Stocks',
    author_email='collinstocks@gmail.com',
    packages=setuptools.find_packages('src'),
    package_data={
        '': ['*.txt', '*.rst', '*.md'],
        'whim.static': ['*', '**/*'],
    },
    package_dir={'': 'src'},
    install_requires=[
        'atomicwrites>=1.3.0,<2',
        'cachetools>=3.1.1,<3.2',
        'fire>=0.2.1,<0.3',
        'requests>=2.22.0,<3',
        'setuptools>=41.2.0,<42',
        'werkzeug>=0.16.0,<1.0',
    ],
    python_requires='>=3.6,<4',
    zip_safe=True,
)
