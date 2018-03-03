# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 12:38:22 2018

@author: 703355681
"""

from context import pacstools

# Instantiate a PacsImportDx object using the default databases
#TODO: this 'if' statement should also ensure that the object is of type
#      'PacsImportDx'
if not('obj' in locals()):
    obj = pacstools.PacsImportDx()

# Attempt to process a singel CR exam
listAcc = list(obj.dataServer.Accession.sample(n=1))
obj.process_exam(listExam=listAcc)
