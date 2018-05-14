#!/usr/bin/env python

import os, shutil, subprocess, sys

this_dir = os.path.abspath(os.curdir)
    
def error(message):
    sys.stderr.write(message)
    os.chdir(this_dir)
    sys.exit(1)

def within_dir(obj, root):

    root = root.rstrip(os.sep)
    if obj.startswith(root):
        return obj[len(root):]
    else:
        return obj

def limbo(name, obj):
    if os.system("limbo -o " + obj + " " + name) != 0:
        error("Failed to compile limbo file: %s\n" % name)

def mkdir(path):
    if not os.path.exists(path):
        print "Creating", path
        os.mkdir(path)

def copy(src, dest):
    print "Copying", src, "to", dest
    shutil.copy2(src, dest)

def move(src, dest):
    print "Moving", src, "to", dest
    shutil.move(src, dest)

def rmtree(path):
    print "Deleting", path
    shutil.rmtree(path)


if __name__ == "__main__":

    if len(sys.argv) < 4:
        sys.stderr.write(
            "Usage: %s <Inferno source directory> <Dis file>... <executable>\n\n"
            "Creates a standalone executable containing the emulator from the specified\n"
            "Inferno source directory, the Dis files for the application and their\n"
            "dependencies.\n\n"
            "If more than one Dis file is given then the first file will be the one\n"
            "run in the Inferno environment. Other files can be additional resources\n"
            "that the application needs.\n" % sys.argv[0]
            )
        
        sys.exit(1)
    
    INFERNO_ROOT = os.path.abspath(sys.argv[1])
    dis_files = map(os.path.abspath, sys.argv[2:-1])
    exec_file = os.path.abspath(sys.argv[-1])
    
    # Include the configuration file in order to get the definitions for the host
    # and object type.
    p = subprocess.Popen(
        ["bash", "-c", "source %s/mkconfig; echo $SYSHOST; echo $OBJTYPE" % INFERNO_ROOT],
        stdout=subprocess.PIPE)
    
    if p.wait() != 0:
        error("Failed to read Inferno configuration. Exiting...\n")
    
    SYSHOST = p.stdout.readline().strip()
    OBJTYPE = p.stdout.readline().strip()
    
    # Locate the appropriate emu subdirectory for the host.
    emu_src_dir = os.path.join(INFERNO_ROOT, "emu", SYSHOST)
    
    tempdir = os.path.join(INFERNO_ROOT, "tmp", "standalone")
    mkdir(tempdir)
    
    # Copy each Dis file into the temporary directory and find its dependencies.
    deps = set()
    dis_names = []
    
    for dis_file in dis_files:
    
        dis_name = os.path.split(dis_file)[1]
        if os.path.splitext(dis_name)[1] != ".dis":
            error("File specified was not a Dis file: %s\n" % dis_file)
        
        dis_names.append((dis_name, dis_file))
        
        copy(dis_file, os.path.join(tempdir, dis_name))
        
        p = subprocess.Popen(["emu", "/dis/disdep", "/tmp/standalone/" + dis_name],
                             stdout=subprocess.PIPE)
        if p.wait() != 0:
            error("Failed to get dependencies for %s. Exiting...\n" % dis_name)
        
        for dep in p.stdout.readlines():
            deps.add(dep.strip())
    
    # Create a new configuration file.
    copy(os.path.join(emu_src_dir, "emu"),
         os.path.join(emu_src_dir, "standalone"))
    
    # Add the Dis files to the configuration file.
    cfg = open(os.path.join(emu_src_dir, "standalone"), "a")
    cfg.seek(0, 2)
    
    # All the Dis files supplied on the command line are included in the root
    # filing system manifest.
    appname = None
    uses_wm = False
    paths = []
    
    for dis_name, dis_file in dis_names:
    
        dis_within = within_dir(dis_file, INFERNO_ROOT)
        
        if dis_within != dis_file:
            path = dis_within
            paths.append((dis_within, dis_within))
        else:
            path = "/dis/standalone/" + dis_name
            paths.append((path, "/tmp/standalone/" + dis_name))
        
        if not appname:
            appname = path
        
        if '/dis/wm' in path:
            uses_wm = True
    
    # Add the dependencies to the manifest.
    for path in deps:
    
        cfg.write('\t%s\n' % path)
        if '/dis/wm' in path:
            uses_wm = True
    
    if uses_wm:
        # The boot.dis file will be renamed to emuinit.dis when packaged.
        # It needs to get a string from the /tmp/appname file which we will
        # include with it.
        paths.append(("/dis/emuinit.dis", "/tmp/standalone/boot.dis"))
        
        # The Dis file in the appname file is used as the entry point into the
        # application.
        open(os.path.join(tempdir, "appname"), "w").write(appname)
        paths.append(("/dis/standalone/appname", "/tmp/standalone/appname"))
        
        # The boot file will replace the emuinit.dis file.
        limbo("boot.b", "boot.dis")
        move("boot.dis", os.path.join(tempdir, "boot.dis"))
    else:
        # The first Dis file is used as the entry point into the application.
        paths[0] = ("/dis/emuinit.dis", paths[0][1])
    
    for dest, src in paths:
        if src == dest:
            cfg.write('\t%s\n' % dest)
        else:
            cfg.write('\t%s\t%s\n' % (dest, src))
    
    cfg.close()
    
    # Enter the Inferno source directory and build the executable.
    os.chdir(emu_src_dir)
    
    if os.system("mk CONF=standalone") != 0:
        error("Failed to build an executable for %s. Exiting...\n" % exec_file)
    
    move("o.standalone", exec_file)
    os.chdir(this_dir)
    
    # Remove the temporary directory.
    rmtree(tempdir)
    
    sys.exit(0)
