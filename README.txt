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

Applications that rely on the window manager to run should include the path of
dis/wm/wm.dis in the list of files to package. The path should be the location
of the file on the host's filing system, referring to the file within in the
Inferno source environment. For example, with INFERNO_ROOT set to the location
of the Inferno environment, the following command should package the drawtest.b
application with the window manager and its dependencies:

    package.py drawtest.b $INFERNO_ROOT/dis/wm/wm.dis drawtest
