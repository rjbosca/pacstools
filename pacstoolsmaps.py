# -*- coding: utf-8 -*-
"""
Created on Sun Jan  7 15:34:26 2018

@author: Ryan
"""

import pandas

#TODO: I need to apply the column type before returning the map to the user

# Data frame map for the DX modality
dictMapDx = {'Accession': str,
             'PatientName': str,
             'PatientSex': 'category',
             'PatientBirthDate': str,
             'Institution': str,
             'InstitutionAddress':   str,
             'StationName': 'category',
             'SeriesDate': str,
             'Protocol': str,
             'StudyDescription': str,
             'SeriesNumber': float,
             'SeriesDescription': str,
             'BodyPart': str,
             'Exposure':                   float,
             'ExposureTime':               float,
             'kVp':                        float,
             'FilterMaterial':             str,
             'FilterMin':                  float,
             'FilterMax':                  float,
             'Grid':                       'category',  #TODO: verify this...
             'ExposureMode':               str,
             'ExposureModeDescription':    str,
             'SID':                        float,
             'ColLeftVertEdge':            float,
             'ColRightVertEdge':           float,
             'ColUpperHorEdge':            float,
             'ColLowerHorEdge':            float,
             'ColVerts':                   str,  # "\" separated integers
             'ColShape':                   str,
             'ExposedArea':                str,  #TODO: verify this
             'ImageProcessingDescription': str,
             'EI':                         float,
             'RelativeEI':                 float,  #TODO: verify this... maybe int16
             'TargetEI':                   float,
             'DI':                         str,
             'Sensitivity':                float,
             'File':                       str}  #TODO: verify this...
dfMapDx = pandas.DataFrame([{'Accession': None,
                             'PatientName': None,
                             'PatientSex': None,
                             'PatientBirthDate': None,
                             'Institution': None,
                             'InstitutionAddress': None,
                             'StationName': None,
                             'SeriesDate': None,
                             'Protocol': None,
                             'StudyDescription': None,
                             'SeriesNumber': None,
                             'SeriesDescription': None,
                             'BodyPart': None,
                             'Exposure': None,
                             'ExposureTime': None,
                             'kVp': None,
                             'FilterMaterial': None,
                             'FilterMin': None,
                             'FilterMax': None,
                             'Grid': None,
                             'ExposureMode': None,
                             'ExposureModeDescription': None,
                             'SID': None,
                             'ColLeftVertEdge': None,
                             'ColRightVertEdge': None,
                             'ColUpperHorEdge': None,
                             'ColLowerHorEdge': None,
                             'ColVerts': None,
                             'ColShape': None,
                             'ExposedArea': None,
                             'ImageProcessingDescription': None,
                             'EI': None,
                             'RelativeEI': None,
                             'TargetEI': None,
                             'DI': None,
                             'Sensitivity': None,
                             'File': None}])

# Data frame map for Sectra PACS
dictMapSectra = {'Accession': str,
                 'PacsScanner': 'category',
                 'PacsServer': 'category',
                 'Modality': 'category'}
dfMapSectra = pandas.DataFrame(columns=list(dictMapSectra.keys()))


# Sectra PACS servers (as of 1/9/2018)
dirsSectraServers = ['\\\\172.25.206.202\\i\\folders',
                     '\\\\172.25.206.203\\i\\folders',
                     '\\\\172.25.206.204\\i\\folders',
                     '\\\\172.25.206.205\\i\\folders',
                     '\\\\172.31.95.206\\i\\folders']
