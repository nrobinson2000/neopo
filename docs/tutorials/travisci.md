# Using Travis CI to Build Neopo Projects

When a neopo project is created with `neopo create`, the project is initialzed as a git repository, and a `.travis.yml` file is created.

Here is an [example project](https://github.com/nrobinson2000/test-neopo-project) and here is it's [Travis CI build page.](https://travis-ci.org/github/nrobinson2000/test-neopo-project)

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

In the `blink` project `src/blink.cpp` contains the application code. You can make additional files in `src/` and add libraries in `lib/` as neccesary, but that is outside the scope of this tutorial.

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

Name the repository `blink`, and leave the box to initilize with a README unchecked.

After clicking the `Create Repository` button you will see some Quick Setup information. In the section titled `…or push an existing repository from the command line` you will see the following commands. 

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/blink.git
git push -u origin master
```

If the push was successfull, you should see your project synced on the GitHub repository page.

## Enabling Travis CI

Next, we will enable Travis CI to build the repository.

[Open this page,](https://travis-ci.org/account/repositories) and sign into Travis CI.

You may need to click the `Sync account` button to get the `blink` repository to show in the list. If you have many repositories, use the `Filter Repositories` box to search for `blink`.

Click the `Settings` button for the `blink` repository in the list to go to the settings page for `blink`.

Click the `Activate Repository` button.

https://travis-ci.org/github/YOUR_GITHUB_USERNAME/blink/settings