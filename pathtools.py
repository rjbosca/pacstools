# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 11:46:58 2017

@author: 703355681
"""

import os


def walk_level(dirIn, level=1, subOnly=True, exclude=[]):
    """walk_level  Walks a directory to a user-specified level

        DIRS = walk_level(DIR) walks the directory DIR to a default depth
        (i.e., 1), returning the sub-directories of DIR.

        DIRS = walk_level(DIR, LEVEL=N) walks the directory DIR as before using
        the user-specified directory depth N, returning only the deepest sub-
        directories. LEVEL must be an integer greater than zero.

        DIRS = walk_level(..., SUBONLY=False) performs as before except all
        sub-directories are returned (not just the deepest ones).

        DIRS = walk_level(..., exclude=[DIR1, DIR2,..., DIRN]) performs as
        described previously, skipping any directories in the list of strings
        "exclude"
        """

    # Original implementation proposed here:
    # https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below

    #TODO: implement wildcards for the EXCLUDE optional input

    #TODO: there should be some validation of the exclude string list provided
    #      by the user to ensure that the strings are not in the requested root
    #      directory...

    # Validate the path
    dirIn = validate_path(dirIn)

    # Validate the input
    assert os.path.isdir(dirIn)
    assert (type(level) == int)
    assert (level > 0)
    assert (type(subOnly) == bool)
    assert (type(exclude) == list)

    # Ensure that EXCLUDE has unique elements
    exclude = list(set(exclude))

    # Count the number of path separators and add this to the user-specified
    # (or default) directory depth. Note that LSTRIP must be used to ignore the
    # separators of UNC paths. This will be to determine when the deepest
    # nested directory level has been achieved.
    exitLevel = dirIn.lstrip(os.sep).count(os.sep) + level

    # Walk the directories returning those values
    #TODO: this seems like code that might result in an infinite loop. Ensure
    #      that proper checks are performed for a level that exceeds the depth
    #      of the sub-directory strucutre.
    catDirs = []
    isExclude = (len(exclude) > 0)
    for root, dirs, files in os.walk(dirIn):

        # Determine if the last level has been reached. This is the current
        # level as determined by the file separators plus 1
        isLastLevel = (exitLevel <= root.lstrip(os.sep).count(os.sep) + 1)

        # Before concatenating the directories, remove any directories that the
        # user requested be removed
        #TODO: implement a case **INSENSITIVE** comparison
        if isExclude:
            listRemove = []
            for d in dirs:
                listRemove.append([d for s in exclude if (d.find(s) != -1)])

            # Unpack the list of directories to remove
            listRemove = [s for sl in listRemove for s in sl]

            # Remove those directories from "dirs"
            for d in listRemove:
                if d in dirs:
                    dirs.remove(d)

        # Concatenate the directories if: (1) all directories are requested or
        # (2) the last level has been reached
        if (not subOnly) or (subOnly and isLastLevel):
            catDirs.extend([os.path.join(root, x) for x in dirs])

        # Modify, in place, the sub-directory list, removing all directories if
        # the exit level has been reached
        if isLastLevel:
            del dirs[:]

    # Return the list of directories
    return catDirs


def validate_path(dirIn):
    """validate_path  Validates and removes trailing path separators

        DIR = validate_path(DIRIN) validates the system specific file
        seperators, removing any trailing white space and separators

        NOTE: Currently, there is no support for unicode directories"""

    assert (type(dirIn) == str)

    # Use the OS tools to validate the path seperators. Also, remove any
    # trailing white spaces
    dirIn = os.fspath(dirIn).rstrip()

    # Replace invalid system specific seperators
    #TODO: this does not account for alternate separators...
    if (os.sep == "/"):
        dirIn = dirIn.replace("\\", "/")
    else:
        dirIn = dirIn.replace("/", "\\")

    # Remove trailing separators
    dirIn = dirIn.rstrip(os.sep)

    return dirIn
