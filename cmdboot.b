implement Boot;

include "sys.m";
    sys: Sys;

include "bufio.m";

include "draw.m";
    draw: Draw;

include "env.m";
    env: Env;

include "string.m";
    str: String;

include "sh.m";
    sh: Sh;

Boot: module
{
    init: fn(ctxt: ref Draw->Context, argv: list of string);
};

init(ctxt: ref Draw->Context, argv: list of string)
{
    env := load Env Env->PATH;
    str := load String String->PATH;
    sys := load Sys Sys->PATH;
    sh := load Sh Sh->PATH;

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

    # Bind the environment device to a directory in the root so that the
    # command line arguments given to the emu can be passed on to the
    # application itself.
    sys->bind("#e", "/env", Sys->MAFTER);

    # Read the emuargs environment variable.
    emuargs := env->getenv("emuargs");
    (emu, app_args) := str->splitl(emuargs, " ");

    # Run the window manager with the file name of the application obtained
    # from the appname file.
    args := list of {"sh", "-c", appname + " " + app_args};

    # We do not need to spawn a new process here.
    sh->init(ctxt, args);
}
