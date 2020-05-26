#!/usr/bin/env python3

import urllib3
import json
import zipfile
import io
import gzip
import tarfile
import platform

DEPS = 'particle/toolchains'
http = urllib3.PoolManager()

def getExtensionURL():
    payload = '{"assetTypes":null,"filters":[{"criteria":[{"filterType":7,"value":"particle.particle-vscode-core"}],"direction":2,"pageSize":100,"pageNumber":1,"sortBy":0,"sortOrder":0,"pagingToken":null}],"flags":103}'
    response = http.request('POST', 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery',
                            body=payload.encode('utf-8'),
                            headers={'accept': 'application/json;api-version=6.0-preview.1;excludeUrls=true',
                                     'content-type': 'application/json'})
    data = json.loads(response.data.decode('utf-8'))
    latest = data['results'][0]['extensions'][0]['versions'][0]['files'][-1]['source']
    return latest


def getManifest():
    url = getExtensionURL()
    response = http.request('GET', url)
    with zipfile.ZipFile(io.BytesIO(response.data), 'r') as vsix:
        content = vsix.read('extension/src/compiler/manifest.json')
        return content


def downloadDep(dep):
    name = dep['name']
    version = dep['version']
    path = name + '/' + version
    path = DEPS + '/' + path
    url = dep['url']
    response = http.request('GET', url)
    data = gzip.decompress(response.data)
    with tarfile.TarFile(None, 'r', io.BytesIO(data)) as file:
        file.extractall(path)

    return response


def getDeps():
    manifest = getManifest()
    data = json.loads(manifest)
    return data


def install():
    osPlatform = platform.system().lower()
    data = getDeps()
    firmware = data['firmware'][0]
    compilers = data['compilers'][osPlatform]['x64'][0]
    tools = data['tools'][osPlatform]['x64'][0]
    scripts = data['scripts'][osPlatform]['x64'][0]
    debuggers = data['debuggers'][osPlatform]['x64'][0]

    downloadDep(firmware)
    downloadDep(compilers)
    downloadDep(tools)
    downloadDep(scripts)
    downloadDep(debuggers)


# make -sf /home/nrobinson/.particle/toolchains/buildscripts/1.9.2/Makefile 
# PARTICLE_CLI_PATH=$(which particle)
# DEVICE_OS_PATH="/home/nrobinson/.particle/toolchains/deviceOS/1.5.2"
# PLATFORM=argon APPDIR=$(pwd) flash-user