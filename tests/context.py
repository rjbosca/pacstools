# -*- coding: utf-8 -*-
"""
Created on Thu Dec 28 14:22:19 2017

@author: Ryan
"""

import os
import sys

# Add the required parent directory to the system path
dirContext = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, dirContext)

# Now that the apporpriate paths are known, import the necessary packages
import pathtools
import pacstools
