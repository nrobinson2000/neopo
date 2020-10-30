from setuptools import setup
from subprocess import run, PIPE

# Consistent version as AUR
count = run(["git", "rev-list", "--count", "HEAD"], stdout=PIPE).stdout.splitlines()[0].decode('utf-8')
commit = run(["git", "rev-parse", "--short", "HEAD"], stdout=PIPE).stdout.splitlines()[0].decode('utf-8')
VERSION = "%s.%s" % (count, commit)
# print(VERSION)

setup(
   name='neopo',
   version=VERSION,
   description='A lightweight solution for local Particle development.',
   author='Nathan Robinson',
   author_email='nrobinson2000@me.com',
   packages=['neopo'],  #same as name
#  install_requires=['foo', 'bar'], #external packages as dependencies
)