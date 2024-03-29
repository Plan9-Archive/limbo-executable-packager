#!/usr/bin/env python

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

import os, shutil, subprocess, sys

this_dir = os.path.abspath(os.curdir)
script_dir = os.path.split(os.path.abspath(__file__))[0]
    
def error(message):
    sys.stderr.write(message)
    os.chdir(this_dir)
    sys.exit(1)

def is_dis(path):
    return path.endswith(".dis")

def find_dependencies(dis_file):

    p = subprocess.Popen(["emu", "/dis/disdep", dis_file],
                         stdout=subprocess.PIPE)
    if p.wait() != 0:
        error("Failed to get dependencies for %s. Exiting...\n" % dis_file)
    
    deps = set()
    for dep in p.stdout.readlines():
    
        if dep.startswith("disdep:"):
            # The disdep tool failed, so indicate this to the caller.
            return None
        
        deps.add(dep.strip())
    
    return deps

def within_dir(obj, root):

    root = root.rstrip(os.sep)
    if obj.startswith(root):
        return obj[len(root):]
    else:
        return obj

def limbo(name, obj):
    print "Compiling", name, "to", obj
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

def has_opt(args, name):
    return ((name in args) and (args.remove(name) or True)) or False

def include_component(dis_path, dest_paths, deps):

    paths = []
    
    if dis_path not in dest_paths and dis_path not in deps:
        paths.append((dis_path, dis_path))
        for path in find_dependencies(dis_path):
            if path not in deps:
                paths.append((path, path))
    
    return paths


if __name__ == "__main__":

    args = sys.argv[:]
    
    draw_project = has_opt(args, "--draw")
    wm_project = has_opt(args, "--wm")
    tk_project = has_opt(args, "--tk")
    
    if len(args) < 4:
        sys.stderr.write(
            "Usage: %s <Inferno source directory> [--draw] [--wm] <Limbo or Dis file>... <executable>\n\n"
            "Creates a standalone executable containing the emulator from the specified\n"
            "Inferno source directory, the Dis files for the application and their\n"
            "dependencies.\n\n"
            "If more than one Dis file is given then the first file will be the one\n"
            "run in the Inferno environment. Other files can be additional resources\n"
            "that the application needs.\n" % sys.argv[0]
            )
        
        sys.exit(1)
    
    INFERNO_ROOT = os.path.abspath(args[1])
    input_files = map(os.path.abspath, args[2:-1])
    exec_file = os.path.abspath(args[-1])
    
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
    
    # Compile any input files that are Limbo files.
    for i, input_file in enumerate(input_files):
    
        if input_file.endswith(".b"):
            dis_file = os.path.join(tempdir, input_file[:-1] + "dis")
            limbo(input_file, dis_file)
            input_files[i] = dis_file
    
    # Copy each Dis file into the temporary directory, if necessary, and find
    # its dependencies.
    deps = set()
    appname = None
    paths = []
    dest_paths = set()
    
    for input_file in input_files:
    
        input_name = os.path.split(input_file)[1]
        input_within = within_dir(input_file, INFERNO_ROOT)
        print input_within, input_file
        
        if input_within != input_file:
            # The file is already in the Inferno source directory.
            src_path = dest_path = input_within
        else:
            src_path = "/tmp/standalone/" + input_name
            dest_path = "/dis/standalone/" + input_name
        
        # Don't include duplicate files.
        if dest_path in dest_paths:
            continue
        
        # Copy the file into the temporary directory if it originates elsewhere.
        if src_path != dest_path:
            copy(input_file, os.path.join(tempdir, input_name))
        elif not os.path.exists(input_file):
            error("Failed to find the requested input file: %s\n" % input_file)
        
        if not is_dis(src_path):
            paths.append((dest_path, src_path))
        else:
            # Only include Dis files if their dependencies can be found.
            new_deps = find_dependencies(src_path)
            
            if new_deps != None:
            
                paths.append((dest_path, src_path))
                deps.update(new_deps)
                dest_paths.add(dest_path)
                
                if not appname:
                    appname = dest_path
            else:
                sys.stderr.write("Failed to find dependencies for input file: %s\n" % input_file)
    
    if appname == None:
        error("Failed to find a module to use as the main application.\n"
              "Perhaps the dependencies for one or more input files could not be determined.\n")
    
    # Add the dependencies to the manifest.
    for path in deps:
        paths.append((path, path))
    
    if tk_project:
        paths += include_component("/dis/lib/tkclient.dis", dest_paths, deps)
    
    if tk_project or wm_project:
    
        # Add the resources required by the window manager and Tk.
        for file_name in os.listdir(os.path.join(INFERNO_ROOT, "icons", "tk")):
            path = "/icons/tk/" + file_name
            paths.append((path, path))
        
        for file_name in os.listdir(os.path.join(INFERNO_ROOT, "fonts", "pelm")):
            path = "/fonts/pelm/" + file_name
            paths.append((path, path))
    
    if wm_project:
    
        # If the application relies on the window manager and it is not
        # included then include the executable and its dependencies.
        paths += include_component("/dis/wm/wm.dis", dest_paths, deps)
        
        # The boot file will replace the emuinit.dis file.
        limbo(os.path.join(script_dir, "wmboot.b"), "boot.dis")
        move("boot.dis", os.path.join(tempdir, "boot.dis"))
        
        # Use the regular configuration file as the basis for the manifest.
        conf_file = "emu"
    
    elif tk_project:
    
        # The boot file will replace the emuinit.dis file.
        limbo(os.path.join(script_dir, "tkboot.b"), "boot.dis")
        move("boot.dis", os.path.join(tempdir, "boot.dis"))
        
        # Use the regular configuration file as the basis for the manifest.
        conf_file = "emu"
    
    else:
        # The boot file will replace the emuinit.dis file.
        limbo(os.path.join(script_dir, "cmdboot.b"), "boot.dis")
        move("boot.dis", os.path.join(tempdir, "boot.dis"))
        
        if draw_project:
            conf_file = "emu"
        else:
            conf_file = "emu-g"
    
    # The boot.dis file will be renamed to emuinit.dis when packaged.
    # It needs to get a string from the /tmp/appname file which we will
    # include with it.
    paths.append(("/dis/emuinit.dis", "/tmp/standalone/boot.dis"))
    paths += include_component("/tmp/standalone/boot.dis", dest_paths, deps)
    
    # The Dis file in the appname file is used as the entry point into the
    # application.
    open(os.path.join(tempdir, "appname"), "w").write(appname)
    paths.append(("/dis/standalone/appname", "/tmp/standalone/appname"))
    
    # Create a new configuration file.
    copy(os.path.join(emu_src_dir, conf_file),
         os.path.join(emu_src_dir, "standalone"))
    
    # Add the Dis files to the configuration file.
    cfg = open(os.path.join(emu_src_dir, "standalone"), "a")
    cfg.seek(0, 2)
    
    # Add the paths to the manifest.
    added = set()
    
    for dest, src in paths:
        if src == dest:
            if dest not in added:
                cfg.write('\t%s\n' % dest)
                added.add(dest)
        elif (dest, src) not in added:
            cfg.write('\t%s\t%s\n' % (dest, src))
            added.add((dest, src))
    
    # Add additional root directories to the manifest.
    cfg.write('\t/n\t/\n')          # /n
    cfg.write('\t/tmp/wdir\t/\n')  # /tmp/wdir
    
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
