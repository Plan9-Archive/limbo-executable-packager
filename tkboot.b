# Copyright (C) 2018 David Boddie <david@boddie.org.uk>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

implement Boot;

include "sys.m";
    sys: Sys;

include "bufio.m";

include "draw.m";
    draw: Draw;
    Context: import draw;

include "sh.m";
    sh: Sh;

include "wmlib.m";
    wmlib: Wmlib;

Boot: module
{
    init: fn(ctxt: ref Context, argv: list of string);
};

init(ctxt: ref Context, argv: list of string)
{
    sys := load Sys Sys->PATH;
    sh := load Sh Sh->PATH;
    wmlib := load Wmlib Wmlib->PATH;

    # Care must be taken to keep these definitions together and not define some
    # above and redefine others here.
    bufio := load Bufio Bufio->PATH;
    Iobuf: import bufio;
    iobuf: ref Iobuf;

    iobuf = bufio->open("/dis/standalone/appname", Sys->OREAD);
    if (iobuf == nil) {
        sys->print("Failed to find the /dis/standalone/appname file. Exiting...\n");
        return;
    }

    appname: string = iobuf.gets('\n');
    if (appname[len(appname) - 1:] == "\n")
        appname = appname[:len(appname) - 1];

    (n, dir) := sys->stat(appname);

    if (n != 0) {
        sys->print("Failed to find the %s file. Exiting...\n", appname);
        return;
    }

    # We could either bind all the things we need into a new directory and
    # bind / to that directory, hiding the non-bound files and directories,
    # or just unmount / to leave the root directory.
    sys->unmount(nil, "/");

    # Run the shell with the file name of the application obtained from the
    # appname file.
    args := list of {"sh", "-c", appname};

    # We do not need to spawn a new process here.
    sh->init(ctxt, args);
}
