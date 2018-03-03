# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 22:12:23 2017

@author: Ryan
"""

import pacstools
import importlib

# Reload the PACSTOOLS module
importlib.reload(pacstools)

# Example path (works on Ryan-PC)
#dirPacs = ["\\\\172.25.206.203\\i\\folders",
#           "\\\\172.25.206.204\\i\\folders",
#           "\\\\172.25.206.205\\i\\folders",
#           "\\\\172.31.95.206\\i\\folders"]
dirPacs = ["\\\\172.25.206.205\\i\\folders"]

# Generate a PACSTOOLS object
obj = pacstools.SectraListener(dirPacs[0])
obj.walk_dirs(exclude=['in_dcm', 'IMS2_magic', 'PREFETCH-2', #172.25.206.203
                       'IMSS1_Magic', 'PREF_IMS3', 'tsm_images', #172.25.206.204
                       'IMSS4_Magic', 'PREFETCH', #172.25.206.205
                       'IDS7_CDImport', 'IDS7_Stacktool', 'PREFETCH', 'PREFETCH1']) #172.31.95.206

# Process random exams (10%) from the current database
listAcc = list(obj.dataServer.Accession.sample(frac=0.001))
#listAcc = ['0405996375']
obj.process_exam(listAcc)

# Finally, update the database
obj._SectraListener__write_database()
