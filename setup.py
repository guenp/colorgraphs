from distutils.core import setup

setup(
	name="Colorgraphs",
	version="1.0",
	author="Guen P",
	author_email="guen@nbi.dk",
    packages=[
        'colorgraphs'
    ],
    license='LICENSE',
    description='Pyqtgraph tools for ipython notebook',
    long_description=open('README.md').read(),
	install_requires=[
        "numpy",
		"pyqtgraph"
	],
)
