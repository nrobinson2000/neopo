#!/usr/bin/env python3

import urllib3
import json
import zipfile
import io
import gzip
import tarfile
import platform
import stat
import os
import pathlib
import sys
import subprocess
import shutil

DEPS = os.environ['HOME'] + '/.particle/toolchains'

http = urllib3.PoolManager()


def getExtensionURL():
    print("Finding Workbench extension URL...")
    payload = '{"assetTypes":null,"filters":[{"criteria":[{"filterType":7,"value":"particle.particle-vscode-core"}],"direction":2,"pageSize":100,"pageNumber":1,"sortBy":0,"sortOrder":0,"pagingToken":null}],"flags":103}'
    response = http.request('POST', 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery',
                            body=payload.encode('utf-8'),
                            headers={'accept': 'application/json;api-version=6.0-preview.1;excludeUrls=true',
                                     'content-type': 'application/json'})
    data = json.loads(response.data.decode('utf-8'))
    latest = data['results'][0]['extensions'][0]['versions'][0]['files'][-1]['source']
    return latest


def getExtension(url):
    print("Downloading Workbench extension...")
    response = http.request('GET', url)
    return zipfile.ZipFile(io.BytesIO(response.data), 'r')


def getFile(file, path):
    content = file.read(path)
    return content


def downloadDep(dep):
    writeManifest(dep)
    name = dep['name']
    version = dep['version']

    print("Downloading dependency " + name + " version " + version + "...")

    path = name + '/' + version
    path = DEPS + '/' + path
    url = dep['url']
    response = http.request('GET', url)
    data = gzip.decompress(response.data)
    with tarfile.TarFile(None, 'r', io.BytesIO(data)) as file:
        file.extractall(path)

    return response


def writeFile(content, path):
    with open(path, 'w') as file:
        file.write(content)


def writeExecutable(content, path):
    with open(path, 'wb') as file:
        file.write(content)
        st = os.stat(file.name)
        os.chmod(file.name, st.st_mode | stat.S_IEXEC)


def getDeps():
    osPlatform = platform.system().lower()
    osArch = 'amd64' if platform.machine() == 'x86_64' else 'arm'

    url = getExtensionURL()
    extension = getExtension(url)

    pathlib.Path(DEPS + '/vscode/').mkdir(parents=True, exist_ok=True)

    manifest = getFile(extension, 'extension/src/compiler/manifest.json')
    particle = getFile(extension, 'extension/src/cli/bin/' +
                       osPlatform + '/' + osArch + '/particle')

    launch = getFile(
        extension, 'extension/src/cli/vscode/launch.json').decode('utf-8')
    settings = getFile(
        extension, 'extension/src/cli/vscode/settings.json').decode('utf-8')

    writeFile(launch, DEPS + '/vscode/launch.json')
    writeFile(settings, DEPS + '/vscode/settings.json')

    writeExecutable(particle, DEPS + '/particle')

    data = json.loads(manifest)
    return data


def writeManifest(dep):
    with open(DEPS + '/manifest.json', 'r+') as file:
        try:
            manifest = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            manifest = {}

        manifest[dep['name']] = dep['version']
        file.seek(0)
        json.dump(manifest, file, indent=4)
        file.truncate()


def createManifest():
    with open(DEPS + '/manifest.json', 'w') as file:
        pass


def loadManifest():
    with open(DEPS + '/manifest.json', 'r') as file:
        return json.loads(file.read())


def install():
    print("Installing neopo...")
    osPlatform = platform.system().lower()
    data = getDeps()
    firmware = data['firmware'][0]
    compilers = data['compilers'][osPlatform]['x64'][0]
    tools = data['tools'][osPlatform]['x64'][0]
    scripts = data['scripts'][osPlatform]['x64'][0]
    debuggers = data['debuggers'][osPlatform]['x64'][0]

    createManifest()
    downloadDep(firmware)
    downloadDep(compilers)
    downloadDep(tools)
    downloadDep(scripts)
    downloadDep(debuggers)


def initProject(path, name):
    tempEnv = os.environ.copy()
    tempEnv['PATH'] += ':' + DEPS

    subprocess.run(['particle', 'project', 'create',
                    path, '--name', name], env=tempEnv)
    pathlib.Path(path + '/' + name +
                 '/.vscode/').mkdir(parents=True, exist_ok=True)

    shutil.copyfile(DEPS + '/vscode/launch.json', path +
                    '/' + name + '/.vscode/launch.json')
    shutil.copyfile(DEPS + '/vscode/settings.json', path +
                    '/' + name + '/.vscode/settings.json')


def configure(projectPath, platform, firmwareVersion):
    with open(projectPath + '/.vscode/settings.json', 'r+') as settings:
        data = json.loads(settings.read())
        data['particle.targetPlatform'] = platform
        data['particle.firmwareVersion'] = firmwareVersion
        settings.seek(0)
        json.dump(data, settings, indent=4)
        settings.truncate()
    print("Configured project " + projectPath + ':')
    print("\tparticle.targetPlatform: " + platform)
    print("\tparticle.firmwareVersion: " + firmwareVersion)


def getSettings(projectPath):
    with open(projectPath + '/.vscode/settings.json', 'r+') as settings:
        return json.loads(settings.read())


def build(projectPath, command):
    manifest = loadManifest()
    compilerVersion = manifest['gcc-arm']
    scriptVersion = manifest['buildscripts']

    tempEnv = os.environ.copy()
    tempEnv['PATH'] += ':' + DEPS + '/gcc-arm/' + compilerVersion + '/bin'

    settings = getSettings(projectPath)
    platform = settings['particle.targetPlatform']
    firmwareVersion = settings['particle.firmwareVersion']

    process = ['make', '-sf', DEPS + '/buildscripts/' + scriptVersion + '/Makefile',
               'PARTICLE_CLI_PATH=' + DEPS + '/particle', 'DEVICE_OS_PATH=' +
               DEPS + '/deviceOS/' + firmwareVersion,
               'PLATFORM=' + platform, 'APPDIR=' + projectPath, command
               ]

    print(process)

    subprocess.run(process, env=tempEnv)

def main():
    print("hello")
    pass



if __name__ == "__main__":
    main()

# neopo help
# neopo install
# neopo configure <platform> <version>

# neopo compile <project>
# neopo flash <project>

# neopo run <command> <project>
