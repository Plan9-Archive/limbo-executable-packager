#!/usr/bin/env python

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


if __name__ == "__main__":

    if len(sys.argv) < 4:
        sys.stderr.write(
            "Usage: %s <Inferno source directory> <Limbo or Dis file>... <executable>\n\n"
            "Creates a standalone executable containing the emulator from the specified\n"
            "Inferno source directory, the Dis files for the application and their\n"
            "dependencies.\n\n"
            "If more than one Dis file is given then the first file will be the one\n"
            "run in the Inferno environment. Other files can be additional resources\n"
            "that the application needs.\n" % sys.argv[0]
            )
        
        sys.exit(1)
    
    INFERNO_ROOT = os.path.abspath(sys.argv[1])
    input_files = map(os.path.abspath, sys.argv[2:-1])
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
    uses_wm = False
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
                
                if '/dis/lib/wm' in dest_path:
                    uses_wm = True
    
    # Add the dependencies to the manifest.
    for path in deps:
    
        paths.append((path, path))
        if '/dis/lib/wm' in path:
            uses_wm = True
    
    if uses_wm:
    
        # If the application relies on the window manager and it is not
        # included then include the executable and its dependencies.
        wm_dis = "/dis/wm/wm.dis"
        
        if wm_dis not in dest_paths and wm_dis not in deps:
            paths.append((wm_dis, wm_dis))
            for path in find_dependencies(wm_dis):
                if path not in deps:
                    paths.append((path, path))
        
        # The boot.dis file will be renamed to emuinit.dis when packaged.
        # It needs to get a string from the /tmp/appname file which we will
        # include with it.
        paths.append(("/dis/emuinit.dis", "/tmp/standalone/boot.dis"))
        
        # The Dis file in the appname file is used as the entry point into the
        # application.
        open(os.path.join(tempdir, "appname"), "w").write(appname)
        paths.append(("/dis/standalone/appname", "/tmp/standalone/appname"))
        
        # The boot file will replace the emuinit.dis file.
        limbo(os.path.join(script_dir, "boot.b"), "boot.dis")
        move("boot.dis", os.path.join(tempdir, "boot.dis"))
        
        # Add the resources required by the window manager.
        for file_name in os.listdir(os.path.join(INFERNO_ROOT, "icons", "tk")):
            path = "/icons/tk/" + file_name
            paths.append((path, path))
        
        for file_name in os.listdir(os.path.join(INFERNO_ROOT, "fonts", "pelm")):
            path = "/fonts/pelm/" + file_name
            paths.append((path, path))
        
        # Use the regular configuration file as the basis for the manifest.
        conf_file = "emu"
    
    else:
        # The first Dis file is used as the entry point into the application.
        paths[0] = ("/dis/emuinit.dis", paths[0][1])
        conf_file = "emu-g"
    
    
    # Create a new configuration file.
    copy(os.path.join(emu_src_dir, conf_file),
         os.path.join(emu_src_dir, "standalone"))
    
    # Add the Dis files to the configuration file.
    cfg = open(os.path.join(emu_src_dir, "standalone"), "a")
    cfg.seek(0, 2)
    
    # Add the paths to the manifest.
    for dest, src in paths:
        if src == dest:
            cfg.write('\t%s\n' % dest)
        else:
            cfg.write('\t%s\t%s\n' % (dest, src))
    
    # Add additional root directories to the manifest.
    cfg.write('\t/n\t/\n')
    
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
