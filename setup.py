from setuptools import setup

import seinfeld

setup(name='seinfeld',
      description='Query a Seinfeld quote database',
      version=seinfeld.__version__,
      author='Amethyst Reese',
      author_email='amy@noswap.com',
      url='https://github.com/amyreese/libseinfeld',
      classifiers=['License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Topic :: Utilities',
                   'Development Status :: 4 - Beta',
                   ],
      license='MIT License',
      packages=['seinfeld'],
      install_requires=['python-dateutil'],
      )
