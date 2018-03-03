# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 00:43:29 2018

@author: Ryan
"""

from context import pacstools
import pacstools_path_test
import py

obj = pacstools_path_test.TestAccessionPathWalk()

# Generate the local path object
d = py.path.local()
accs, nIms = obj._gen_dirs(d)

# Generate the the Sectra object
obj = pacstools.SectraListener(d.strpath, dirDataBase=d.strpath)
obj.walk_dirs()

# Remove the temporary path
d.join('folders').remove()
