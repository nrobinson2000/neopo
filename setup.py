import platform
from setuptools import setup
from subprocess import run, PIPE

running_on_windows = platform.system() == "Windows"

# Consistent version as AUR
count = run(["git", "rev-list", "--count", "HEAD"], stdout=PIPE).stdout.splitlines()[0].decode('utf-8')
commit = run(["git", "rev-parse", "--short", "HEAD"], stdout=PIPE).stdout.splitlines()[0].decode('utf-8')
VERSION = "%s.%s" % (count, commit)
# print(VERSION)

share_files = [
   ('/usr/share/bash-completion/completions', ['completion/neopo']),
   ('/usr/share/licenses/neopo', ['LICENSE']),
   ('/usr/share/man/man1', ['man/neopo.1']),
   ('/usr/share/neopo/scripts', ['scripts/POSTINSTALL'])
]

script_unix = ['scripts/unix/neopo', 'scripts/unix/neopo-script', 'scripts/unix/particle']
script_windows = ['scripts/windows/neopo.cmd', 'scripts/windows/neopo-script.cmd', 'scripts/windows/particle.cmd']
script_files = script_windows if running_on_windows else script_unix

setup(
   name='neopo',
   version=VERSION,
   description='A lightweight solution for local Particle development.',
   author='Nathan Robinson',
   author_email='nrobinson2000@me.com',
   url='https://github.com/nrobinson2000/neopo',
   packages=['neopo'],
   data_files=share_files if not running_on_windows else None,
   scripts=script_files
)