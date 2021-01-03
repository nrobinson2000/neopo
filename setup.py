import os
from platform import system
from setuptools import setup
from subprocess import run, PIPE, CalledProcessError

running_on_windows = system() == "Windows"

# Consistent version as AUR
try:
    count = run(["git", "rev-list", "--count", "HEAD"],
            stdout=PIPE, check=True).stdout.splitlines()[0].decode('utf-8')
    commit = run(["git", "rev-parse", "--short", "HEAD"],
            stdout=PIPE, check=True).stdout.splitlines()[0].decode('utf-8')
    VERSION = "%s.%s" % (count, commit)
except CalledProcessError:
    print("Could not determine package version with Git! Exiting...")
    raise

# Additional files for *nix: completion, man page, etc.
share_files = [
   ('/usr/share/man/man1', ['man/neopo.1']),
   ('/usr/share/licenses/neopo', ['LICENSE']),
   ('/usr/share/neopo/scripts', ['scripts/POSTINSTALL']),
   ('/usr/share/bash-completion/completions', ['completion/neopo'])
]

# WIP: Don't includes share_file on Windows or when installing as non-root
if running_on_windows:
    share_files=None
else:
    if os.geteuid() != 0:
        share_files=None

script_unix = ['scripts/unix/neopo',
    'scripts/unix/neopo-script',
    'scripts/unix/particle']

script_windows = ['scripts/windows/neopo.cmd',
    'scripts/windows/neopo-script.cmd',
    'scripts/windows/particle.cmd']

script_files = script_windows if running_on_windows else script_unix

setup(
   name='neopo',
   version=VERSION,
   description='A lightweight solution for local Particle development.',
   author='Nathan Robinson',
   author_email='nrobinson2000@me.com',
   url='https://github.com/nrobinson2000/neopo',
   packages=['neopo'],
   data_files=share_files,
   scripts=script_files
)
