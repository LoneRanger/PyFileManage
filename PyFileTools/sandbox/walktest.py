#!/usr/bin/python
"""
"""
import os, sys, time, difflib
print "starting run"
dir = "/home/kurt"

start_time = time.time()
print "*" * 25, "  running module  ", "*" * 25 #debug
print "started at", time.localtime(start_time)

def walk_down(top, callback):
    """Walks a tree down from top making a call for each directory.

    Walk a file structure from top to bottom not looking for paths to ignore.
    The idea is to make a generic reusable function rather than provide a
    specific solution. Any results need to be done in the callout as all this
    does is just walk through the tree passing on the results of the callout.
    """
    import os
    results = {}
    for root, dirs, files in os.walk(top):
        abs_root = os.path.abspath(root)
        #doit = "%s(abs_root,dirs,files)"% callback
        #results[os.path.abspath(root)] = eval(doit) #exec doit #
        results[os.path.abspath(root)] = callback(abs_root, dirs, files)
    return results
# ^ returns results, a dictionary key=root value=(eval(doit))
def get_stats(root, dirs, files):
    """Do something with the data passed to its paramaters.


    os.stat(  path) Perform a stat() system call on the given path. The return
    value is an object whose attributes correspond to the members of the stat
    structure, namely:

    00  st_mode (protection bits)
    01  st_ino (inode number)
    02  st_dev (device)
    03  st_nlink (number of hard links)
    04  st_uid (user ID of owner)
    05  st_gid (group ID of owner)
    06  st_size (size of file, in bytes)
    07  st_atime (time of most recent access)
    08  st_mtime (time of most recent content modification) With *nix the time
                    reported by ls -l
    09  st_ctime (platform dependent; time of most recent metadata change on
                    Unix, or the time of creation on Windows)

    The ST_MODE can yeild more information using the stat module to determine
    the following where mode is the ST_MODE value:

    S_ISDIR(  mode) Return non-zero if the mode is from a directory.
    S_ISCHR(  mode) Return non-zero if the mode is from a character special
                device file.
    S_ISBLK(  mode) Return non-zero if the mode is from a block special device
                file.
    S_ISREG(  mode) Return non-zero if the mode is from a regular file.
    S_ISFIFO(  mode) Return non-zero if the mode is from a FIFO (named pipe).
    S_ISLNK(  mode) Return non-zero if the mode is from a symbolic link.
    S_ISSOCK(  mode) Return non-zero if the mode is from a socket.

    Two additional functions are defined for more general manipulation of the
    file's mode:

    S_IMODE(  mode) Return the portion of the file's mode that can be set by
        os.chmod()--that is, the file's permission bits, plus the sticky bit,
        set-group-id, and set-user-id bits (on systems that support them).

    S_IFMT(  mode) Return the portion of the file's mode that describes the file
        type (used by the S_IS*() functions above).
    """
    root_stat = os.stat(root)
    files_stats = {}
    for file in files:
        abs_file = os.path.join(root, file)
        if os.path.exists(abs_file):
            file_stat = os.stat(abs_file)
            files_stats[abs_file] = file_stat
        else:
            files_stats[abs_file] = 0
    return (root_stat, files_stats)
# ^ returns (root_stat, files_stats)
def check_sizes(root, dirs, files, limit=2**31):
    """Check file sizes reporting anything over the limit.

    The root and dirs values are not needed but included for consistancy alone.
    The correctness of the absolute file path is dependent on the root value
    passed to this function.
    """
    toobig = []
    for file in files:
        abs_file = os.path.join(root, file)
        if os.path.exists(abs_file):
            file_stat = os.stat(abs_file)
            if file_stat[6] >= limit:
                print  "%s over the limit @ %dB."% (abs_file, file_stat[6])
                toobig.append(abs_file)
    return toobig
# ^ returns toobig, a list of all files larger than 'limit'
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
        if not tentry.isreg():
            print "not!"
            continue
        k = (tgz, tentry.name)
        tstats[k] = (
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
        tbshlfname = os.path.splitext(tgz)[0]
        shelf_add(tbshlfname + "_shelf", k, tstats[k])
    return tstats
# ^ returns tstats
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
#treedb = walk_down(dir, get_stats)
#tarball = "/media/hda9/BlackBartHome_070107.tar.gz"
#tarball_stats = get_tarball_stats(tarball)
#tbshlfname = os.path.splitext(tarball)[0]
#shelf_make(tbshlfname + "_" + "shelf", tarball_stats)

#keys = treedb.keys()

#for key in keys:
#    print "\n directory is", key, "value is", treedb[key][0]
#    items = treedb[key][1]
#    for item in items:
#        print "file %s has stats...\n %s"% (item, items[item])

large = walk_down("/media/hda9", check_sizes)

end_time = time.time()
print "\nended at", time.localtime(end_time)
print "this run took", end_time - start_time, "seconds",
print " or", (end_time - start_time)/60, "minutes."
print "*" * 25, "That's all folks. end of run", "*" * 25 #debug
