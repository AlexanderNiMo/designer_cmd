import os
from importlib.machinery import SourceFileLoader

from pkg_resources import parse_requirements
from setuptools import find_packages, setup

module_name = 'designer_cmd'

module = SourceFileLoader(
    module_name, os.path.join(module_name, '__init__.py')
).load_module()


def load_requirements(fname: str) -> list:
    requirements = []
    with open(fname, 'r') as fp:
        for req in parse_requirements(fp.read()):
            extras = '[{}]'.format(','.join(req.extras)) if req.extras else ''
            requirements.append(
                '{}{}{}'.format(req.name, extras, req.specifier)
            )
    return requirements


with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=module_name,
    version=module.__version__,
    author=module.__author__,
    author_email=module.__email__,
    license=module.__license__,
    description='Пакет для автоматизации взаимодействия с пакетным режимом 1С.',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/AlexanderNiMo/designer_cmd',
    platforms='Windows',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: Russian',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    python_requires='>=3.6',
    packages=find_packages(exclude=['tests']),
    install_requires=load_requirements('requirements.txt'),
    include_package_data=True,
    test_suite='designer_cmd.tests',
)
