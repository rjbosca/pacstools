# -*- coding: utf-8 -*-
"""
Created on Wed Jan  3 11:09:41 2018

@author: 703355681
"""

import py
import pacstools_path_test

obj = pacstools_path_test.TestAccessionPathWalk()

# Generate the local path object
d = py.path.local()
accs, nIms = obj._gen_dirs(d)

# Remove the temporary directory
d.join('folders').remove()
