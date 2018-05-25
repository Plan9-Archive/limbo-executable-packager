Standalone Executable Packager for Limbo Programs
=================================================

Summary
-------

When run, the package.py script performs the following tasks:

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
the --wm option. Those that also use the Tk module to create a user interface
should be packaged using the --tk option instead. Applications that only rely
on the draw module should be packaged using the --draw option. Those that do
not rely on any of these resources can omit these options.

For example, with INFERNO_ROOT set to the location of the Inferno environment,
the following command should package the windowtest.b application with the
window manager and its dependencies:

   package.py --wm $INFERNO_ROOT windowtest.b windowtest

This should cause a windowtest executable to be created. This should run as a
standalone application. The executable file can also be reduced in size by
processing it with the strip utility:

    strip windowtest

This should result in a substantially smaller file.


License
-------

This software is licensed under the Expat/MIT license:

  Copyright (C) 2018 David Boddie <david@boddie.org.uk>

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to
  deal in the Software without restriction, including without limitation the
  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
  sell copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  DEALINGS IN THE SOFTWARE.
