Standalone Executable Packager for Limbo Programs
=================================================

 1. Compiles Limbo files using the limbo executable.
 2. Copies Dis files and any other listed resources into the Inferno source
    environment.
 3. Finds the dependencies of the Dis files.
 4. Determines whether the window manager Dis files are required.
   a) Copies a boot file and a text file to the environment to set up the
      window manager before running the application specified in the text file.
 5. Adds the Dis files to the manifest.
 6. Builds a variant of the emu application.

Applications that rely on the window manager to run should be packaged using
the --wm option. Those that only rely on the draw module should be packaged
using the --draw option.

For example, with INFERNO_ROOT set to the location of the Inferno environment,
the following command should package the drawtest.b application with the window
manager and its dependencies:

    package.py --wm $INFERNO_ROOT drawtest.b drawtest
