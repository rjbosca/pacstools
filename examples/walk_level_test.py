# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 16:29:16 2017

@author: Ryan
"""

import pathtools
import importlib

# Reload pathtools
importlib.reload(pathtools)

# Example path (works on Ryan-PC)
dirWalk = "D:\\pacs_testing\\folders"

# Walk the directory one level. This will return all of the scanner directory
# names assuming that a Sectra PACS directory structure is used. NOTE: the
# walk_level function will automatically validate the directory
dirSectra = pathtools.walk_level(dirWalk)
print("Walked the to the first level of: ", dirWalk)
print(*dirSectra, sep="\n")
print("\n")

# Walk the directory through the accession number level(=2), returning only the
# accession number sub-directories.
dirSectraLvl2 = pathtools.walk_level(dirWalk, level=2)
print("Accession numbers in: ", dirWalk)
print(*dirSectraLvl2, sep="\n")
print("\n")

# Walk the directory through the accession number level(=2), returning all sub-
# directories.
dirSectraLvl2 = pathtools.walk_level(dirWalk, level=2, subOnly=False)
print("All sub-directories of: ", dirWalk)
print(*dirSectraLvl2, sep="\n")
print("\n")

# Walk the same directory as the previous test, ignoring any directory that
# contains US or OT
dirSectraLvl2 = pathtools.walk_level(dirWalk, level=2, subOnly=False, 
                                     exclude=["US", "RF"])

print("All sub-directories of (ignoring US and RF): ", dirWalk)
print(*dirSectraLvl2, sep="\n")
print("\n")