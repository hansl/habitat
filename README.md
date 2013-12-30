
# Habitat

A heaven for your environments to grow.

# Technical Design
^DRAFT


# Objectives

Habitat makes managing your runtime environment easier. When creating a virtual environment, or simply when needing to start multiple servers at the same time, it becomes cumbersome to manually manage scripts and servers.


# Example

Say you have a virtual environment with a list of python packages, nodes packages and a Django application with a MySQL server used locally that all needs to be more or less automatically updated across multiple computers (either in production or development). NPM is a mess to manage by itself, and 

You normally create your environments like this:

    $ virtualenv $VIRTUAL_ENV
    ...
    $ source $VIRTUAL_ENV/bin/activate
    ...
    $ pip install --upgrade -r$DEPS_FILE
    ...
    $ cd $VIRTUAL_ENV && npm install $PACKAGE_JSON
    ...
    ## Later when running the Django app
    $ mysql-server & && ./manage.py runserver

And so on. Normally you would start the MySQL server on a separate console to be able to kill it if needed. When running a node package (like Karma for your frontend unittests), it becomes impossible to keep the correct environment variables in place.

With Habitat, you build a python script that will automatically create, install, upgrade and start the different pieces of your environment. You then can export a single file script that will setup the proper Habitat dependencies on any new computer, whether Linux or Mac. All you need is a python interpreter.

An example of such a script is as follow:

    #!python
    from habitat import *
    import os.path
    import sys
    
    class MyHabitat(Habitat):
        components = [
            VirtualEnv,
            Pip,
            Npm,
            DjangoApp
        ]

        env_root = '~/my_project/habitat/%(env_name)'
        # Would be deduced if it wasn't specified.
        git_root = os.path.dirname(os.path.abspath(__file__))
        pip_deps = '%(git_root)/deps/(%env_name)'
        npm_package = '%(git_root)/deps'
        django_manage_path = '%(git_root)/manage.py'

        def __init__(self, *args):
            super(MyHabitat, self).__init__(*args)
            if self['hermetic']:
                self.deps.append(MySqlServer)

    MyHabitat(sys.argv)
    

From there you simply run:

    $ ./my_habitat.py

And it will do the rest. It will figure out a root for your virtualenv, based on the environment name that you're already in. If the virtualenv binary is not available, a message will tell you that you need to install it using your package manager of choice. Then it will run PIP inside your environment. The `env` variable will be replaced by the name of the current environment, which you can configure to be production, staging, beta, dev or any name you want. By default most of these values are taken from OS environment variables.

Finally, when starting the script in a hermetic environment it will check if MySQL server is installed and if not install and configure it using a set of defaults. The configuration of the environment can be set using OS variables or settings inside the script. Then it will use the Django manage script to start the Django server.

All of these components are not necessarily in order. There is a dependency list that will determine the exact order in which everything will be executed. Also, if certain components are not installed some other components might or might not behave properly. A good example is the Pip component, which will install everything inside the virtualenv if the component is used, while using the system python library if not.

# API

## Habitats

The `Habitat` class define a series of parameters to use for your configuration. The Habitat instance is passed to each components during each phases.

## Components

The library of components is really large, and it will grow rather fast. Here's a simple list of the most commonly used:

### Installers

  * `VirtualEnv`. Use the `virtualenv` script to create and activate an environment. Normally virtualenv should be provided by the system, but in case it is not Habitat can download, configure and make the binary inside the habitat.
  
  * `Pip`.
  
  * `Npm`.
  
  * `Bower`.
  
### Servers

  * `MySqlServer`.
  

### Misc

  * `DjangoApp`.


--

# Internals

## Habitat

### Phases

An habitat has 4 phases:

* Version check [`version_phase(self)`], including installing or upgrading components. Takes all the components and their versions, in order of dependencies. If a current version is not provided, the component is assumed to not be installed and the component installation is called. If an installation is performed, an update will not be performed on that component and it will be assumed to be the version reported by that component.

* Running. Start each components respecting the dependencies. If a component fails to update

* Report. Capture the output/input of each components' executed command lines and store it.

* Stop. 

### API

A habitat class provides methods for components to interact within the habitat. These include the following:

* `has(self, ComponentClass)`. Whether a habitat has a component.

* `exec(self, command_line)`. 


## Component

A component should define the following methods:

* `install(self)`. It is the habitat job to know if a component is installed or not. Calling `version()` is in itself not enough. This method here should install the component in the Habitat (whether the system or 

* `update(self)`. 

* `start(self)`. 

* `stop(self)`.

* `version(self)`. Returns a `LooseVersion`/`StrictVersion` instance or a string that represents the _currently installed_ version of the component. Please note that because Habitat uses LooseVersion most of the time, the following is true: `1.2.0-rc1` > `1.2.0`. To resolve this conflict we do a manual check for the `rc` string and if true we could install an "inferior" version, only if it does have an "rc" string in it which is unlikely.

* `bin(self)`. Lookup the binary in the component. This is useful for components that install additional binaries that can be run from the command line. Should return None if the path is not found, and an array (or tuple) if there's more than one binary in the component.

* `env(self, env)`. Modify an OS environment in which some components will be run. When running a command line executable, the Habitat will generate an environment from all the components necessary to execute


## Metadata

Meta data is normally stored inside a file. It can be human readable or not. For example, the PIP component expect a pip_deps path that contains a list of PIP packages to install and may (or not) contain a version number. If the version is specified, it will store this version in the Habitat metadata, otherwise it'll simply store the list of individual packages and their version, and increment if that list changes.

Along components, the Habitat itself keeps a version list through a metadata file in the habitat root. The file is called `habitat.metadata` and should not be read by anyone else than the root `Habitat` class.

The way Metadata is used is through the MetadataFile class. By creating an instance of that file 

