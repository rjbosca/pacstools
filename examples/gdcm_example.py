# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 23:53:32 2018

@author: Ryan
"""

# This script is an example of using GDCM to provide the appropriate data type

import gdcm

f = 'E:\\images\\pacs_testing\\folders\\CR_IMS2\\0405296098\\0\\im_1\\i0000,0000b.dcm'

r = gdcm.Reader()
r.SetFileName(f)
if not r.Read():
    raise NotADirectoryError(f)

f = gdcm.PythonFilter()
f.SetFile(r.GetFile())
t = gdcm.Tag(0x0018, 0x0060)

ds = r.GetFile().GetDataSet()

# The code contained in the print statement causes the kernel to die...
#print(f.ToPyObject(t))

# The following code attempts to discover ever DICOM meta data element
tag = []
for i in range(1, 65535):
    for j in range(1, 65535):
        t = gdcm.Tag(i, j)
        if ds.FindDataElement(t):
            tag.append((hex(i), hex(j)))
            print(f'Tag {len(tag)} found: {tag[-1]}')
    print(hex(i))
print('Header dump complete!')