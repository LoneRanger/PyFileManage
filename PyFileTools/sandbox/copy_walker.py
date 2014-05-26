#!/usr/bin/python
"""Copy Files & Trees.

"""
import os, sys, filecmp, time, shutil

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
# ^ Copies tree at src to dst, dst must not already exist.
def copy_file(src, dst):
    """Copies a file from src to dst where dst is directory or filename.

    The dst can be a directory or file name. If dst is a relative path it needs
    to be relative to the current working directory. Using a fully qualified
    file name or absolute path is recommended. If a directory, the dst directory
    must already exist.
    """
    import shutil
    if os.path.isdir(src):
        try:
            shutil.copy2(src, dst)
        except IOError, e:
            print e
    else:
        print src, "is not a valid filename or can't be found."
# ^ copies file 'src' to directory or file at 'dst'
def file_tree_walker(top, ignore=[], seq=(), args=[], dict={}):
    """Walk through a filesystem tree from top down.

    This function can also ignore some branches if desired. It can also take or
    ignore a sequence and/or a list of arguments.
    """
    import os, sys, re, tarfile, zipfile # insure needed modules are available
    print '\nstarting file_tree_walker() at', top
    norm_files = []
    tar_files = []
    zip_files = []
    link_files = []
    broken_files = []
    no_read_files = []
    stats = []
    for root, dirs, files in os.walk(top): # take a walk through 'top'
        if root not in ignore:
            for file in files: # loop through files in current root directory
                filename = root + "/" + file # make a fully qualifed name
                if not os.path.exists(filename): # check exist
                        broken_files.append(filename)
                else:
                    if os.access(filename, os.R_OK): # check permission
                        # TODO: Fix the tarfile and zipfile features
                        #if tarfile.is_tarfile(filename): # Is it a tarball?
                        #    tar_files.append(filename) # Yes, so add to list
                        #elif zipfile.is_zipfile(filename): # Is it a zip file?
                        #    zip_files.append(filename) # Yes, so add to list
                        if os.path.islink(filename): # Is it a link?
                            link_files.append((filename, os.readlink(filename)))
                        elif os.path.isfile(filename):
                            norm_files.append(filename)
                        if os.path.exists(filename):
                            stat = os.stat(filename) # get stats for current file
                            stats.append((filename, stat))
                    else:
                        no_read_files.append(filename)
    print "done with file_tree_walker()."
    return (norm_files,     # normal files
            tar_files,      # files that are tarballs
            zip_files,      # files that are zip files
            link_files,     # files that are links to other files
            broken_files,   # files that are broken links
            no_read_files,  # files exist but no read permission
            stats)     # all files that are not broken with stats on each
# ^ returns norm_files,tar_files,zip_files,link_files,stats

def sync_walker(src, dst, ignore=[]):
    """ Walks a source and destination  tree syncing destination with source.

    Works similar to copy_tree() except destination can already exist.
    """
    file_missing =     [] # hold fq names of missing files
    file_identical =   [] # hold results of comparing files
    file_fraternal =   [] # hold exist but stats different
    file_zero_length = [] # hold zero length file
    dir_missing =      [] # hold src directories missing from dst
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
        for root, dirs, files in os.walk(src): #We be walkin' the src directory.
            root_dst = root.replace(src, dst) # path of equivalent dst directory
            if os.path.exists(root_dst): # does it exist?
                dc = filecmp.dircmp(root, root_dst) # instanciate dircmp
                for file in files:
                    src_file = os.path.join(root, file) # make fully qualifed
                    dst_file = os.path.join(root_dst, file)
                    if os.path.exists(dst_file): # destination exists
                        if os.path.getsize(src_file) > 0:
                            #print "dst file is", dst_file
                            if filecmp.cmp(src_file, dst_file):
                                file_identical.append(src_file)
                            else: # same name different stats
                                file_fraternal.append(src_file)
                                copy_file(src_file, dst_file) #Copies the file
                        else: # it is a zero length file
                            file_zero_length.append(src_file)
                    else: # destination does not exist.
                        #print "##there is no %s file" % dst_file
                        file_missing.append(src_file)
            else: # The equivalent root directory did not exist.
                #print "#There is no %s directory." % root_dst
                # If the directory is missing all the files are missing too.
                copy_tree(root, root_dst)
                dir_missing.append(root)
                for file in files:
                    src_file = root + "/" + file
                    file_missing.append(src_file)
            #print "** at %s diff is %s" % (root, dc.diff_files)
        compare = [dir_missing,
                   file_identical,
                   file_fraternal,
                   file_missing,
                   file_zero_length]
        return compare
# ^ returns compare, [dir_missing, file_identical, file_fraternal, file_missing]

src = "/media/HD-HCU2-1/Media/ogg"
dst = "/media/sdb3/ogg"

