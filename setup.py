import os
from platform import system
from setuptools import setup
from subprocess import run, PIPE, CalledProcessError

running_on_windows = system() == "Windows"
running_in_docker = os.path.isfile("/.dockerenv")

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

# Skip share_files on Windows, docker, or when installing as non-root
if running_on_windows or running_in_docker or os.geteuid() != 0:
    share_files=None

# Provide neopo, neopo-script, and particle commands
script_unix = ['scripts/unix/neopo',
    'scripts/unix/neopo-script',
    'scripts/unix/particle']

script_windows = ['scripts/windows/neopo.cmd',
    'scripts/windows/neopo-script.cmd',
    'scripts/windows/particle.cmd']

script_files = script_windows if running_on_windows else script_unix

# update version.py
with open(os.path.join('neopo', 'version.py'), 'w') as file:
    file.writelines(['NEOPO_VERSION="%s"' % VERSION])

setup(
   name='neopo',
   version=VERSION,
   description='A lightweight solution for local Particle development.',
   long_description="""
   Neopo is a Particle development management utility that simplifies the
   installation and usage of Particle's toolchains on a variety of distributions.
   It features options to build or flash projects, iterable commands, a scripting
   interface, and Particle Workbench/CLI compatibility.""",
   author='Nathan Robinson',
   author_email='nrobinson2000@me.com',
   url="https://neopo.xyz",
   download_url='https://github.com/nrobinson2000/neopo',
   license="MIT",
   packages=['neopo'],
   platforms=["Linux", "macOS", "Windows", "ARM"],
   data_files=share_files,
   scripts=script_files
)
