#!/usr/bin/python
""" Some crude tools for file management.

The copy tools are crude in the sense that they don't make any sophisticated
decisions about replacing existing files and directories. At this point if you
need sophisticated search or replacement tools you will need to build them
yourself.

TODO: There can be permission issues in reading and writing files.
    Needs work arounds or exception handeling. Some instances may requrie
    running sudo or as root.
"""
import os, sys, filecmp, time, shutil
from pprint import pprint
from os.path import join, getsize
from types import *
print "\n\tstarting run"
start_time = time.time()
t = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(start_time))
print "running", t

## Globals ##
test_print = "/home/kurt/bin/Test/test_print.txt"
test_copy = "/home/kurt/bin/Test/test_copy.txt"

#### Functions ####
## Compare ##
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
        for root, dirs, files in os.walk(src):
            root_dst = root.replace(src, dst) # path of equivalent dst directory
            if os.path.exists(root_dst): # does it exist?
                dc = filecmp.dircmp(root, root_dst) # instanciate dircmp
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(root_dst, file)
                    if os.path.exists(dst_file):
                        if os.path.getsize(src_file) > 0:
                            #print "dst file is", dst_file
                            if filecmp.cmp(src_file, dst_file):
                                file_identical.append(src_file)
                            else: # same name different stats
                                file_fraternal.append(src_file)
                        else: # it is a zero length file
                            file_zero_length.append(src_file)
                    else:
                        #print "##there is no %s file" % dst_file
                        file_missing.append(src_file)
            else:
                #print "#There is no %s directory." % root_dst
                # If the directory is missing all the files are missing too.
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
def dir_comp(src, dst):
    """Compare trees with filecmp.dircmp()"""
    dc = filecmp.dircmp(src, dst)
    dc.report_full_closure()
# ^ uses filecmp.dircmp(src, dst).report_full_closure()
def compare_files_md5sums(sizes):
    """ Compare md5 of files of the same size.

    This only works for comparing files in a filesystem with other files in a
    filesystem and DOES NOT work for entries in a tarball.
    As is, this function is designed to receive a dictionary of files with size
    as key and list of one or more fully qualified filenames for each value.

    Consider breaking this apart into smaller functions.
    Consider using md5sum of just first 64K of file.
    """
    import md5
    print "Comparing hashes."
    duplicates = {}
    for key in sizes.keys(): # loop through entire dict by key
        if len(sizes[key]) > 1: # if more than one file per key
            temp = {} # reset temp dictionary per key
            # get md5 for each file with this key (size)
            for file in sizes[key]: # loop through each file
                md5 = md5sum(file) # get md5 for file
                if temp.has_key(md5): # temp if key (md5) exists
                    #temp[md5].append(file) # yes so append new file
                    temp[md5].append(file) # add file to temp[md5]
                else:
                    temp[md5] = [file] # wasn't there so add file
            for key in temp.keys():
                if len(temp[key]) > 1:
                    duplicates[key] = temp[key]
        else: # there was only one file that size so no duplicates
            pass
    return duplicates # dict of identical files, key = md5, value = filenames
# ^ returns duplicates by comparing full md5sums
## Manipulate ##
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
def merge_tree(src, dst):
    """Merges src files and directories into dst.


    TODO: Needs testing before regular use!
    """
    import filecmp, shutil
    for root, dirs, files in os.walk(src):
        print "root is", root
        root_dst = root.replace(src, dst) # equivalent dst directory to root
        if not os.path.isdir(root_dst): # if the dst root doesn't exist?
            copy_tree(root, root_dst) # recursively create it w/copy_tree()
            continue # that's it for this trip through the loop
        else:
            for file in files: # for files in root directory
                src_file = os.path.join(root, file) # make fully qualified name
                dst_file = os.path.join(root_dst, file) # fully qualified name
                # source exists and is not zero length
                if not os.path.exists(src_file):
                    print "The %s file doesn't exist." % src_file
                    continue
                if not os.path.getsize(src_file) > 0: # catch 0 length files
                    print "The file %s has zero length." % src_file
                    continue
                if not os.path.exists(dst_file): # destination exist?
                    try:
                        #os.system('cp ' + src_file + " " + dst_file)
                        shutil.copy2(src_file, dst_file) # copy
                    except IOError, e:
                        print "error", e
                    continue
                if not filecmp.cmp(src_file, dst_file):
                    try:
                        #os.system('cp ' + src_file + " " + dst_file)
                        shutil.copy2(src_file, dst_file) # copy
                    except IOError, e:
                        print "error", e

# ^ copy src directories and files into dst recursively overwriting & creating
def replace_tree(src, dst):
    """Replaces the dst tree with the src tree.

    If the dst directory already exists it will be removed and then replaced by
    the src directory. This is potentialy dangerous, no checks are made to
    insure dst exists before removing src.
    TODO: Needs testing! Use with caution when testing.
    """
    import shutil
    shutil.rmtree(dst)
    shutil.copytree(src, dst)
# ^ replaces dst with src
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
def dicts_merge(d0, d1):
    """Merge two dictionaries without overwriting the originals.

    This version does not alter the original dictionaries values to be merged.
    If the record (key) exists in both dictionaries the values are put in a list
    and added. This is desired when the original values need to be kept intact.
    """
    newdict = {}
    k0 = d0.keys() # keys from d0
    k1 = d1.keys() # keys from d1
    keys = list(set(k0 + k1)) # unique set of combined keys
    for key in keys:
        if d0.has_key(key) and d1.has_key(key): # dictionaries have same key?
            value = [d0[key]] + [d1[key]]
        elif d0.has_key(key) and not d1.has_key(key):
            value = d0[key]
        elif d1.has_key(key) and not d0.has_key(key):
            value = d1[key]
        else:
            print "Error, you shouldn't ever get here."
        value.sort()
        newdict[key] = value
    return newdict
# ^ returns newdict a dictionary with combined values
def make_dirs(seq):
    """Make directory(s) from sequence of directory names with mode.

    The sequence needs to be directory names relative to current directory or
    they need to be fully qualified names. If the directory already exists this
    function will silently skip that directory. Using os.makedirs() any
    intermediate level directories will be created if they do not already exist.
    It is OK if seq is a single name value or a name/number pair.
    ie ("/path/to/dir", 0755)...
    """
    from types import StringType # import * is allowed only in module level!
    for dir in seq:
        if len(dir) == 2: # does the sequence hold more than just a name?
            name = dir[0]
            num = eval(str(dir[1]))
            if os.path.isdir(name):
                print "The directory, %s already exists." % name
                continue
            # is it a string and a valid octal mode number?
            if type(name) == StringType and 0 < num < 01000:
                os.makedirs(name, num)
        if os.path.isdir(dir):
            continue
        os.makedirs(dir)
# ^ creates new directory(s) ## Unfinished ##
## Hashes ##
def md5sum( filename ):
    """ Compute md5 (Secure Hash Algorythm) of a file.

    Input : filepath : full path and name of file
    Output : string : contains the hexadecimal representation of the md5
    of the file, or returns '0' if file could not be read
    (file not found, no read rights...)
    """
    import md5
    try:
        f = open(filename,'rb')
        m = md5.new()
        data = f.read(65536)
        while len(data) != 0:
            m.update(data)
            data = f.read(65536)
        f.close()
    except:
        return '0'
    else:
        return m.hexdigest()
# ^ returns m.hexdigest() a md5sum of entire file
def short_md5(filename):
    """ Compute md5 sum of 1st 64K of a file by file's name.

    Input : file : full path and name of file
    Output : string : contains the hexadecimal representation of the MD5
    of the file, or returns '0' if file could not be read
    (file not found, no read rights...)
    """
    import md5
    try:
        f = open(filename)
        m = md5.new()
        data = f.read(65536)
        m.update(data)
        f.close()
    except:
        return '0'
    else:
        return m.hexdigest()
# ^ returns m.hexdigest(), a md5sum of first 64K of entry
def short_tar_extract(tgz, entry):
    """ Compute md5 sum of 1st 64K of a file like object.

    Input : fobj a file like object
    Output : string : contains the hexadecimal representation of the MD5
    of the file, or returns '0' if file could not be read
    (file not found, no read rights...)
    """
    import tarfile
    tar = tarfile.open(tgz)
    fobj = tar.extractfile(entry)
    short_content = fobj.read(65536)
    tar.close()
    return short_content
# ^ returns short_content
def content_md5sum(content):
    """Returns md5sum of a chunk of data.

    Calculates the md5sum of the data it is passed. Should usually be a small
    chunk consisting of the first 64K of a regular file's content.
    >>> import md5
    >>> m = md5.new()
    >>> m.update("Nobody inspects")
    >>> m.update(" the spammish repetition")
    >>> m.digest()
    """
    import md5
    m = md5.new()
    m.update(content)
    md5sum = m.hexdigest()
    return md5sum
# ^ returns md5sum, the md5 hash of data passed to this function
#### Pickle & Shelve ####
def pickle_put(filename,obj):
    """ saves object to file by pickling

    file = file where object is to be saved
    filename = name of file
    dict = the dictionary to be saved

    requires:
        import cPickle <module>
        passed filename <string>
        passed obj <dictionary>
        local file <file>
    """
    import cPickle
    file = open( filename, "w" )
    cPickle.dump( obj, file )
    file.close()
# ^ pickles object at fully qualified filename
def pickle_get(filename):
    """Retrieves an object that was saved using the cPickle module.

    The assumption is the file represented by 'filename' is a valid file and
    that it contains a valid cPickle object. It does not include a mechanism to
    validate that assumption.
    """
    import cPickle
    file = open(filename, "r")
    obj = cPickle.load(file)
    file.close
    return obj
# ^ returns obj, the pickled object at filename
def shelf_make(name, obj, flag="c"):
    """Make new shelf from dictionary object.

    I suppose it could be any type of object as long as an iteration of the
    object provides a string followed by an object that can be pickled. For the
    purpose this function was intended the object should be a dictionary with a
    string used for keys and an arbitrary object as the value.
    """
    import shelve
    shobj = shelve.open(name, flag)
    for key in obj:
        shobj[str(key)] = obj[key] # assign insuring key is a string
    shobj.close()
# ^ puts a dictionary object in a shelf
def shelf_add( name, key, value, flag="c" ):
    """ Add or replace a single key/value pair in a shelf object.

    Using name as relative or fully qualified path/name write a key/value pair
    to disk. The name should *not* include an extension. If there is already a
    shelf with the same name and key that key will be overwritten.
    The key must be a string and the value can be any object that one could
    pickle.
    """
    import shelve
    shobj = shelve.open(name, flag)
    shobj[str(key)] = value # assign insuring key is a string
    shobj.close()
# ^ stores key/value pair in shelf replacing an existing value
def shelf_get_record(name, key, flag="r"):
    """retrieve a value from a single record from shelf using key.

    Since the key is already known there is no need to return anything but the
    value stored under that key. If key does not exist return 'None' without
    failing.
    """
    import shelve
    shobj = shelve.open(name)
    value = shobj.get(key)
    shobj.close()
    return value
# ^ returns value
def shelf_get_keys(name, flag="r"):
    """get just the keys of a shelf.

    read all the keys and only the keys of a shelf"""
    import shelve
    shobj = shelve.open(name, flag)
    keys = shobj.keys()
    shobj.close()
    return keys
# ^ returns keys
def shelf_get_all(filename):
    """Retrieves an entire shelf object.

   This function retrieves an entire shelf by calling it with a fully qualified
   file name of the shelf conaining the desired object. It doesn't care
   anything about the object other than it needs to fit the criteria of any
   shelved object. If the filename doesn't exist it returns, 'None'.
   """
    import shelve
    if os.path.isfile(filename): # make sure filename exists
        shobj = shelve.open(filename) # open shelved object
        obj = dict(shobj) # turns instance into dictionary
        shobj.close() # close shelved object
        return obj
    pass # did not exist so will silently return None
# ^ retruns obj from shelf, filename
## Misc Utilities ##
def file_stats_walker(top, ignore =[]):
    """ Walks a tree from top to bottom getting info on each file.

    In its current incarnation it makes a dictionary with each fully qualifed
    file name as the key and the file stats and the results of the GNU 'file'
    command as the value. The os.stat() return value is an object whose
    attributes correspond to the members of the stat structure, namely: st_mode
    (protection bits), st_ino (inode number), st_dev (device), st_nlink (number
    of hard links), st_uid (user ID of owner), st_gid (group ID of owner),
    st_size (size of file, in bytes), st_atime (time of most recent access),
    st_mtime (time of most recent content modification), st_ctime (platform
    dependent; time of most recent metadata change on Unix, or the time of
    creation on Windows)
    """
    file_info = {}
    for root, dirs, files in os.walk(top): # take a walk
        if root in ignore: # skip if in ignore
            continue
        else:
            for file in files:
                filename = os.path.join(root, file)# make a fully qualifed name
                if file or filename in ignore: # skip if in ignore
                    continue
                file_stat = os.stat(filename)
                file_type = os.popen('file ' + filename).read() # use *nix file
                magic = file_type.split(':')[1].strip() # split & use 2nd part
                file_info[filename] = (file_stat, magic)
    return file_info
# ^ returns stats, a dictionary key=filename value=st
def get_file_stats(seq):
    """Return stats on each file in sequence 'seq'

    The sequence should be either basenames of files in current directory or
    fully qualified file names. This function returns a list of tuples that
    contain a ( filename, stats ) pair.
    """
    import os
    stats = []
    for file in files:
        try:
            stat = os.stat(file)
            stats.append((file, stat))
        except IOError, e:
            print e
            continue
    return stats
# ^ return stats, a list of tuples of file/stat pairs
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
## consider just using file_stats_walker instead and removing this one
def get_tarball_stats(tgz):
    """Retrieve stats of tarball's component items.

    Note:

    name     Name of the archive member.
    size     Size in bytes.
    mtime    Time of last modification.
    mode     Permission bits.
    type     File type. type is usually one of these constants: REGTYPE,
                AREGTYPE, LNKTYPE, SYMTYPE, DIRTYPE, FIFOTYPE, CONTTYPE,
                CHRTYPE, BLKTYPE, GNUTYPE_SPARSE. To determine the type of a
                TarInfo object more conveniently, use the is_*() methods below.
    linkname Name of the target file name, which is only present in TarInfo
                objects of type LNKTYPE and SYMTYPE.
    uid      User ID of the user who originally stored this member.
    gid      Group ID of the user who originally stored this member.
    uname    User name.
    gname    Group name.
 A TarInfo object also provides some convenient query methods:
 isfile(  ) Return True if the Tarinfo object is a regular file.
 isreg(  )  Same as isfile().
 isdir(  )  Return True if it is a directory.
 issym(  )  Return True if it is a symbolic link.
 islnk(  )  Return True if it is a hard link.
 ischr(  )  Return True if it is a character device.
 isblk(  )  Return True if it is a block device.
 isfifo(  ) Return True if it is a FIFO.
 isdev(  )  Return True if it is one of character device, block device or FIFO.
    """
    tstats = {} # initialize new emply dictionary
    import tarfile # insure tarfile module is imported
    tar = tarfile.open(tgz, "r") # open tarball for reading
    for tentry in tar:
        tstats[(tgz, tentry.name)] = (
                                      tentry.size,      # 0
                                      tentry.mtime,     # 1
                                      tentry.mode,      # 2
                                      tentry.type,      # 3
                                      tentry.linkname,  # 4
                                      tentry.uid,       # 5
                                      tentry.gid,       # 6
                                      tentry.uname,     # 7
                                      tentry.gname,     # 8
                                      )
    return tstats
# ^ returns tstats
def tar_entry_stats_walker(tgz):
    """use tarfile to retrieve stats of tarball's component items.

    Note: This function is not a standard walk function but is called that
    since iterating through the tar object has basicaly the same result.
    This function creates a dictionary of each components stats with the
    size as a key and the components name and other stats as the value in
    the form of a tuple. See tstat assignment below for the order and
    nature of each stat. The use of the dictionary in this function groups
    together items in the tarball by size to help mark which files are
    potentially duplicated.
    """
    tar_entry_stats = [] # all items name and other stats
    tar_sizes = {} # initialize new emply dictionary
    import tarfile # insure tarfile module is imported
    tar = tarfile.open(tgz, "r") # open tarball for reading
    tgz_stat = os.stat(tgz)
    for taritem in tar: # go through each entry in tarball
        tname  = taritem.name # get name of entry
        tsize  = taritem.size # get size of entry
        ttime  = taritem.mtime # Time of last modification
        tmode  = taritem.mode # Permission bits
        ttype  = taritem.type # file type
        tlink  = taritem.linkname # Name of the target file name
        tuid   = taritem.uid # User ID
        tgid   = taritem.gname # Group ID
        tuname = taritem.uname # User name
        tgname = taritem.gname # Group name
        if taritem.isfile():
            tstat  = (tgz,    # Location/name of tar file
                    tname,    # Name of the archive member
                    tsize,    # Size in bytes
                    ttime,    # Time of last modification
                    tmode,    # Permission bits
                    ttype,    # file type
                    tlink,    # Name of the target file name
                    tuid,     # User ID
                    tuname,   # Group ID
                    tgname)   # Group name
            tar_entry_stats.append(tstat) # append to list
        key = tsize
        if key > 0: # not directory or 0 length file
            if tar_sizes.has_key(key): # already has record in dictionary
                value = tar_sizes[key]
                value.append(tname)
            else:
                tar_sizes[key] = [tname] # makes value a list & assign to key
        else:
            pass
    tar.close()
    return tar_entry_stats, tar_sizes
# ^ returns tar_entry_stats, tar_sizes
def zip_entry_walker(zip):
    """Retrieves information about entries in zip file, zip

    This function is similar to the tar_entry_stats_walker function.
    """
    import zipfile
    zip_sizes = {}
    zip_entry_stats = []
    zfile = zipfile.Zipfile(zip)
    names = zfile.namelist()
    for name in names:
        info = zfile.getinfo(name)
        dayTime = info.date_time
        size = info.file_size
        key = size
        if key > 0:
            if zip_sizes.has_key(key):
                value = zip_sizes[key]
                value.append(repr(name))
            else:
                zip_sizes[key] = [name]
        else:
            pass
        zip_entry_stats.append((name, size, dayTime))
    zfile.close
    return zip_entry_stats, zip_sizes
    #content = zfile.read(name)
# ^  zip_entry_stats, returns zip_sizes
def seq_files_by_size(seq):
    """Make a dictionary with key = size and value = fully qualified filename.

    The seq parameter should be a sequence of tuples consisting of a fully
    qualifed filename and the stats for that file.
    [('/path/name1, (n0, n1, ... n9)), ('/path/name2, (n0, n1, ... n9))]
    n0 = ST_MODE -- Inode protection mode.
    n1 = ST_INO --- Inode number.
    n2 = ST_DEV --- Device inode resides on.
    n3 = ST_NLINK - Number of links to the inode.
    n4 = ST_UID --- User id of the owner.
    n5 = ST_GID --- Group id of the owner.
    n6 = ST_SIZE -- Size in bytes of a plain file; amount of data waiting on
                    some special files.
    n7 = ST_ATIME - Time of last access.
    n8 = ST_MTIME - Time of last modification.
    n9 = ST_CTIME - The ``ctime'' as reported by the operating system. On some
                    systems (like Unix) is the time of the last metadata change,
                    and, on others (like Windows), is the creation time (see
                    platform documentation for details).
    """
    dict = {}
    for item in seq:
        key = item[1][6]
        if key > 0: # not directory or 0 length file
            if dict.has_key(key): # already has record in dictionary
                value = dict[key]
                value.append(item[0])
            else:
                dict[key] = [item[0]] # makes value a list & assign to key
        else:
            pass
    return dict
# ^ returns dict, a dict key = size of file, value = list of file names
def append_string2file(string, filename):
    """Append a string to a text file"""
    file = open(filename, "a")
    file.write(string)
    file.close()
# ^ append a string to text file
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
# ^ returns source and destination ## Unfinished ##

#top_a = "/media/hda7"
#top_b = "/media/disk/BlackBartHda20080925/hda7"
#top_a = "/home/kurt/bin/Test/dir-a"
#top_b = "/home/kurt/bin/Test/other/dir-b"
src = "/home/kurt" #top_a #"/media/HD-HSIU2/hdb3" #
dst = "/media/hdb3/BlackBartHomeBackup20080826"
#top_b #"/media/hda7/backup/hdb3" #
## v tar stuff v
#tarball = "/home/kurt/bin/Test/test.tgz"
#tarstatsdb, tarsizesdb = tar_entry_stats_walker(tarball)

print "src is %s  \ndst is %s" % (src, dst)
#copy_tree(src, dst) ## NOTE: To work dst must NOT already exist!
#merge_tree(src, dst)

results = compareTrees(src, dst)
pickle = os.path.join(dst, "compare_results.obj")
pickle_put(pickle, results)
#
#merge_tree(src, dst)

dir_awol   = results[0]
file_ident = results[1]
file_frat  = results[2]
file_awol  = results[3]
file_zero  = results[4]
print """ In dst there are...
 %-10d missing directories
 %-10d identical files
 %-10d files with different stats
 %-10d missing files
 %-10d zero length files
""" % (len(dir_awol),
       len(file_ident),
       len(file_frat),
       len(file_awol),
       len(file_zero))

n = len(results)
for x in range(n):
    print "results[%d] length is %d" % (x, len(results[x]))

#dir_comp(src, dst)

end_time = time.time()
print "\nended at", time.localtime(end_time)
print "this run took", end_time - start_time, "seconds",
print " or", (end_time - start_time)/60, "minutes."
print "*" * 25, "That's all folks. end of run", "*" * 25 #debug
