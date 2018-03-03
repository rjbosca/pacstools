# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 15:51:18 2018

@author: Ryan
"""

import SimpleITK

f = 'E:\\images\\pacs_testing\\folders\\CR_IMS2\\0405296098\\0\\im_1\\i0000,0000b.dcm'

r = SimpleITK.ImageFileReader()
r.LoadPrivateTagsOff()
r.SetFileName(f)
img = r.Execute()

print(len(img.GetMetaDataKeys()))
#for k in img.GetMetaDataKeys():
#    val = r.GetMetaData(k).replace(')', '').replace(' ', '')
#    print(f'{k} | {val}')

# Another implmentation
r = SimpleITK.ReadImage(f)
print(len(r.GetMetaDataKeys()))
for k in r.GetMetaDataKeys():
    val = r.GetMetaData(k).replace(')', '').replace(' ', '')
#    print(f'{k} | {val}')
    print(f'({k})')

# Note that these implementations provide the same result