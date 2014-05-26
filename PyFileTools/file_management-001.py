#!/usr/bin/python
""" Compare uncompressed backuped directories and files.

Walk through both file structures making a comparison of files on the way. I see
this as providing some default actions, such as just checking if any files or
directories are different and the differences would be noted or actually taking
action to modify files and directories. The primary scenarios would be...

Copy in one direction only.
    * Just copy files not present in the source to the destination.
    * Delete files in the destination that were not found in the source.

Sync structures by merging in both directions.
    * Select files that are newer and sync newest versions deleting old
    * Keep all versions in both and renaming as needed

Report on differences without action

Include/exclude directories and files

Advanced features to go here or other module...
Restore directories or individual files from list(s)
Rename files
Move files
Politeness, do in the background and/or scheduled time in large or small blocks
Preserve or change permissions.
Copy links yes/no which/how
"""
import os, sys, filecmp, time

from pprint import pprint
from os.path import join, getsize
import shutil
print "starting run"
start_time = time.time()
print "started at", time.localtime(start_time)
## Globals ##
test_print = "/home/kurt/bin/Test/test_print.txt"
test_copy = "/home/kurt/bin/Test/test_copy.txt"

#topa = "/media/hdb3/"
#topb = "/media/HD-HSIU2/hdb3/"
#
alta = "/home/kurt/bin/Test/dir-a"
altb = "/home/kurt/bin/Test/other/dir-b"
def itsRelative(path_source, path_destination):
    """ Walk a source and destination tree simultaniously.

    Uses os.walk() to itterate down the source tree while also itterating
    through a previoulsy saved backup of the source tree in a different
    location. WORKS BUT SEE todo BELOW...
    TODO: Still needs exception and error mechanisms.
    TODO: Fails silently if path_source doesn't exist.
    """
    print" Starting itsRelative() function."
    print "source is =", path_source
    print "destination is", path_destination
    for root_source, dirs_source, files_source in os.walk(path_source):
        relative_path = root_source.replace(path_source, "")
        root_destination = root_source.replace(path_source, path_destination)
        print "\nroot_source =", root_source
        print "root_destination =", root_destination
        for file in files_source:
            source_file = os.path.join(root_source, file)
            destination_file = os.path.join(root_destination, file)
            copy = 0
            s = ''
            if os.path.isfile(destination_file):
                if filecmp.cmp(source_file, destination_file):
                    copy = 0# files are identical, no need to copy
                else:
                    copy = 1 # not identical, so copy
                    s = source_file + " -- does not match --\n"
                    append_string2file(s, test_print)
                    print s
            else:
                copy = 1 # not there so copy
                s =  source_file + " ## NOT IN DESTINATION ##\n"
                append_string2file(s, test_print)
                print s
            if copy: # copy if not there or not the same
                print "source_file =", source_file
                print "destination_file =", destination_file
                #shutil.copy2(source_file, destination_file)
                s = source_file + " @@would have been copied@@\n"
                append_string2file(s, test_copy)
## ^ UNFINISHED
def append_string2file(string, filename):
    """Append a string to a text file"""
    file = open(filename, "a")
    file.write(string)
    file.close()
## ^ append a string to text file
def inputURI(in_src, in_dst):
    """Get user input for source and destination URIs.

    At this point only local files are considered but this should be easy to
    modify by changing the os.path.isdir()test to accept remote locations.
    TODO: Rewrite with nested functions for user input to avoid recalling the
    entire function. If destination is not correct and accepted just the
    destination need be re-entered.
    """
    def confirm_src(in_src):
        """confirm or change default source directory"""
        print "user confirmation"
        print "\n\t The default source is ->", in_src
        print "\t Enter 'y' to accept or..."
        print "\t enter an alternate local file location"
        print "\t or 'q' to quit"
        scr_ans = raw_input("\t => ")
        if scr_ans.lower() == "q":
            print "Happy trails!"
            exit()
        elif scr_ans.lower().startswith('y'):
            print "\n You accepted %s as the default source." % (in_src, )
            print "returning", in_src
            return in_src
        else:
            if os.path.isdir(scr_ans): # is it a valid directory?
                out_src = scr_ans # yes, so apply it
                return scr_ans
            else:
                print "I can't find", scr_ans,
                print "please make sure it exists and is available."
                print "now in_src =", in_src
                confirm_src(in_src)
    def confirm_dst(in_dst):
        """confirm or change default destination directory"""
        print "\n\t The default destination is ->", in_dst
        print "\t Enter 'y' to accept or..."
        print "\t enter an alternate local file location"
        print "\t or 'q' to quit"
        dstanswer = raw_input("\t => ")
        if dstanswer.lower() == "q":
            print "Happy trails!"
            exit()
        elif dstanswer.lower().startswith('y'):
            print "\n You accepted %s as the default destination." % (in_dst, )
            return in_dst
        else:
            if os.path.isdir(dstanswer):
                out_dst = dstanswer
            else:
                print "I can't find", dstanswer,
                print "please make sure it exists and is available."
                confirm_dst(in_dst)
    def confirm_final(src, dst):
        """final confirmation of source & destination directories"""
        print "\n\t Now just one more time to make sure we have it right..."
        print "\t The source is...\t", src
        print "\t and the destination is...\t", dst
        finalanswer = raw_input("\t is this correct? [Yes/No] ")
        if finalanswer.lower().startswith("y"):
            print"\n Alright, fasten your seat belt, here we go..."
            return src, dst
        else:
            if not finalanswer.lower().startswith('y'):
                inputURI(dflt_source, dflt_destination)
    src = confirm_src(in_src)
    dst = confirm_dst(in_dst)
    print "src =", src
    print "dst =", dst
    return confirm_final(src, dst)

## ^ returns source and destination
def compareTrees(src, dst):
    """ Compares a source tree 'src' against destination tree 'dst'.

    This function checks to insure that both the source and the destination
    directories exist before calling dircmp. This avoids an error and returns a
    message about what happened.

    Currently this uses the source (src) as the reference point and only checks
    for files and directories in one direction. If there are files or
    directories in the destination (dst) that aren't in the source they will not
    be reported. This may change later or perhaps just rerun this check with
    source and destination reversed.
    """
    import filecmp
    file_missing = [] # hold fq names of missing files
    file_identical =   [] # hold results of comparing files
    file_fraternal = [] # hold exist but stats different
    dir_missing = [] # hold src directories missing from dst
    srcX = os.path.isdir(src) # boolian true if src exists as a directory
    dstX = os.path.isdir(dst) # boolian true if dst exists as a directory
    # first check the status of the root src and dst directores to be compared
    print "srcX is %s and dstX is %s" % (srcX, dstX)
    if not srcX or not dstX: # is either one of them unavailable?
        if not srcX and not dstX:
            e = "Neithier %src nor %dst directores can be found." % (src, dst)
        elif not dstX:
            e = "The backup directory %s can't be found" % (dst, )
        elif not srcX:
            e = "The source directory %s can't be found" % (src, )
        return e
    else: # both exist so let's compare them
        abpth_src = os.path.abspath(src) # absolute path of src
        abpth_dst = os.path.abspath(dst) # absolute path of dst
        dirname_src = os.path.dirname(abpth_src)
        print "dirname_src is", dirname_src
        dirname_dst = os.path.dirname(abpth_dst)
        print "dirname_dst is", dirname_dst
        for root, dirs, files in os.walk(src):
            relative_path = root.replace(src, "") # get relative path of root
            print "relative_path is", relative_path
            root_dst = root.replace(src, dst) # path of equivalent dst directory
            print "     root_dst is", root_dst
            if os.path.exists(root_dst): # does it exist?
                dc = filecmp.dircmp(root, root_dst) # instanciate dircmp
                for file in files:
                    src_file = root + "/" + file
                    dst_file = root_dst + "/" + file
                    if os.path.exists(dst_file):
                        #print "dst file is", dst_file
                        if filecmp.cmp(src_file, dst_file):
                            file_identical.append(src_file)
                        else:
                            file_fraternal.append(src_file)
                    else:
                        #print "##there is no %s file" % dst_file
                        file_missing.append(src_file)
            else:
                #print "#There is no %s directory." % root_dst
                dir_missing.append(root)
                for file in files:
                    src_file = root + "/" + file
                    file_missing.append(src_file)
            #print "** at %s diff is %s" % (root, dc.diff_files)
        compare = [dir_missing, file_identical, file_fraternal, file_missing]
        return compare, dirname_src, dirname_dst
## ^ check if filesystem tree's exist and are current
def dir_comp(src, dst):
    """Compare trees with filecmp.dircmp()"""
    dc = filecmp.dircmp(src, dst)
    dc.report_full_closure()
## ^ uses filecmp.dircmp(src, dst).report_full_closure()
def copy_tree(src, dst):
    """Copy a complete tree from src to dst

    To work src must exist and dst must not exist.
    """
    import shutil
    if not os.path.exists(src):
        e = "Error, source is not available!"
        print e
        return e
    elif os.path.exists(dst):
        e = "Error, destination already exists!"
        print e
        return e
    else:
        shutil.copytree(src, dst, symlinks = True)
## ^ Copies tree at src to dst, dst must not already exist.

print "let's go........"
src = alta #"/media/hdb5"
dst = altb #"/media/HD-HSIU2/hdb5"
#results, fq_src, fq_dst = compareTrees(src, dst)
print "src is %s  \ndst is %s" % (src, dst)
results, fq_src, fq_dst = compareTrees(src, dst)

print "results[0] =", results[0]
print "results[1] =", results[1]
print "results[2] =", results[2]
print "results[3] =", results[3]

dir_awol   = results[0]
file_ident = results[1]
file_frat  = results[2]
file_awol  = results[3]

print "source was", fq_src
print "destination was", fq_dst

#dir_comp(src, dst)

end_time = time.time()
print "\nended at", time.localtime(end_time)
print "this run took", end_time - start_time, "seconds",
print " or", (end_time - start_time)/60, "minutes."
print "*" * 25, "That's all folks. end of run", "*" * 25 #debug
