from setuptools import find_packages, setup


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


install_requires = parse_requirements('requirements.txt')
setup(
    name='powerpoint_generative_ai',
    packages=find_packages(),
    version='0.1.4',
    license='MIT',
    description='Library written by Width.Ai. Streamlines the utilization of GPT models for automatic PowerPoint content generation. Also offers semantic searches on slide content, enabling you to quickly pinpoint relevant information',
    author='Patrick Hennis',
    author_email='patrick@width.ai',
    url='https://github.com/Width-ai/powerpoint-generative-ai',
    download_url='https://github.com/Width-ai/powerpoint-generative-ai/archive/refs/tags/v0.1.4.tar.gz',
    keywords=['LLM', 'Semantic Search', 'PowerPoints'],
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
