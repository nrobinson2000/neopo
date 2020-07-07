# Using Travis CI to Build Neopo Projects

When a neopo project is created with `neopo create`, the project is initialized as a git repository, and a `.travis.yml` file is created.

Here is an [example project](https://github.com/nrobinson2000/blink) and here is it's [Travis CI build page.](https://travis-ci.org/github/nrobinson2000/blink)

To use Travis CI to automatically run build tests for a project, the project must first be synced with a repository on GitHub.

## Creating the Project

Let's create a project with neopo. In this tutorial our project will be called `blink`.

```bash
$ neopo create blink

$ cd blink
```

Inside of the `blink` project you should find the following structure:

```
.git/
.gitignore
project.properties
README.md
src/
.travis.yml
.vscode/
```

You will be writing your code in the `src/` directory.

The `.git/` directory means that the project is a git repository.

Project settings are stored in the `.vscode/` directory.

The `.travis.yml` file is used to define the settings for Travis CI.

## Configuring the Project

By default, projects are configured for the Argon device and the latest deviceOS version. If you wish to configure your project for a different device platform and deviceOS version you can use the `configure` command, where PLATFORM and VERSION are your desired device platform and deviceOS version.

```
$ neopo configure PLATFORM VERSION
```

## Writing some code

The project is initialized with a blank application in the `src/` directory. Let's write some code to make the onboard LED blink.

In the `blink` project `src/blink.cpp` contains the application code. You can make additional files in `src/` and add libraries in `lib/` as necessary, but that is outside the scope of this tutorial.

Open `src/blink.cpp` with Vim or your preferred editor:

```
$ vim src/blink.cpp
```

Replace the contents of the file with the following for a simple blink application, or write any code that you like.

```cpp
#include "Particle.h"

void setup() {
    pinMode(D7, OUTPUT);
}

void loop() {
    digitalWrite(D7, HIGH);
    delay(1000);
    digitalWrite(D7, LOW);
    delay(1000);
}
```

Save and close the file, and then add the changes to files in the project to git and commit them.

```bash
$ git add -A
$ git commit -m "initial commit"
```

## Syncing with GitHub

Create a new repository on GitHub on [this page.](https://github.com/new)

Name the repository `blink`, and leave the box to initialize with a README unchecked.

After clicking the `Create Repository` button you will see some Quick Setup information. In the section titled `…or push an existing repository from the command line` you will see the following commands. 

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/blink.git
git push -u origin master
```

If the push was successful, you should see your project synced on the GitHub repository page.

## Enabling Travis CI

Next, we will enable Travis CI to build the repository.

[Open this page,](https://travis-ci.org/account/repositories) and sign in to Travis CI.

You may need to click the `Sync account` button to get the `blink` repository to show in the list. If you have many repositories, use the `Filter Repositories` box to search for `blink`.

Click the `Settings` button for the `blink` repository in the list to go to the settings page for `blink`.

Click the `Activate Repository` button.

## Triggering a Travis CI build

Anytime that you commit and push to GitHub, Travis CI will run the tests again. Let's make some changes to the project.

Open `README.md` in the `blink` project. At the top of the file, you will see some markdown to display a Travis CI badge for your project.

```
[![](https://api.travis-ci.org/yourUser/yourRepo.svg?branch=master)](https://travis-ci.org/yourUser/yourRepo)
```

Replace `yourUser/yourRepo` in both the SVG link and the page link to your GitHub username followed by `/blink`. For me, it would be `nrobinson2000/blink`.

Add the changes to git, commit, and push them:

```bash
$ git add -A
$ git commit -m "update readme"
$ git push -u origin master
```

## Watching a Travis CI build

If you go back to the Travis CI page for your project and click on the `Build History` tab you see the list of builds. A yellow build is currently running. Click on the latest build. Once the build starts, you can watch the Job Log to view the commands running and the output. If all the commands were successful the build turns green. If any commands failed the build turns red.

## Changing Travis CI settings

When neopo initializes a project it uses the following `.travis.yml` file:

```yml
# Build a neopo project with Travis CI
os: linux
language: shell
install:
  - export PATH="$PATH:$PWD"
  - sudo apt update
  - sudo apt install libarchive-zip-perl libc6-i386
  - curl -LO https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo
  - chmod +x neopo
  - neopo install
script:
  - neopo build
cache:
  directories:
    - $HOME/.particle
    - $HOME/.neopo
```

With these settings, Travis CI will perform a minimal install of neopo and then run commands specified in the `script` section. By default, Travis CI will only run `neopo build`, but you can add additional commands as you please.

Perhaps you want to test building for multiple devices? With Travis CI this is easy. Simply run `neopo configure` and `neopo build` for each device.

```yml
script:
  - neopo configure argon 1.5.2
  - neopo build
  - neopo configure boron 1.5.2
  - neopo build
  - neopo configure photon 1.5.2
  - neopo build
```

## Using Neopo scripts

If you want to simplify the `.travis.yml` file you can write a [neopo script](../full-docs.md#script) that tests the project and tell Travis CI to use that script instead of writing a long list commands in YML format.

The Travis CI script above can be written in a neopo script like the following (comments added):

```py
# Configure and build for argon
configure argon 1.5.2
build

# Configure and build for boron
configure boron 1.5.2
build

# Configure and build for photon
configure photon 1.5.2
build
```

To use this script with Travis CI save it to a file in the project. I saved it to `blink/testDevices`. To use the script in Travis CI, change the `script` section of `.travis.yml` to the following:

```yml
script:
  - neopo load testDevices
  - neopo script testDevices
```

This will tell Travis CI to use neopo to load the `testDevices` script and then run it.

## Conclusion

Travis CI is an excellent tool for running tests and verifying that Particle projects can build successfully. I hope that you can make use of it in your projects. I have used Travis CI for several years on many projects and it continues to be an amazing, reliable service.

## More Reading

Documentation Links:

- [Travis CI Docs](https://docs.travis-ci.com/)
- [Neopo Docs](../full-docs.md)
- [Particle Docs](https://docs.particle.io/)