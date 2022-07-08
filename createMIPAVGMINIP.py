# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 11:09:08 2020

@author: anmorrow
"""

import easygui
import pydicom
import numpy as np
import random
import os
import sys
import subprocess
from os import listdir
from os.path import isfile, join


"""this helps order the files"""
def slicenum(fname):
    fname = fname[0:-4]
    temp = fname[::-1]
    lastpos = -1*temp.find(".")
    slice = int(fname[lastpos:])
    return slice

"""get the list of files"""
try:
    mypath = easygui.diropenbox("Choose the directory where the CT data are stored")
except:
    easygui.msgbox("Please enter a valid directory")
    sys.exit()
    
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
onlyfiles.sort(key=slicenum)   
fullnames=[]
zPosArray = []
groups = []

"""get the z locs of all files"""
for i in range(len(onlyfiles)):
    fullnames.append(join(mypath, onlyfiles[i]))
    dp = pydicom.dcmread(fullnames[i])
    zPosArray.append(float(dp.ImagePositionPatient[2]))

"""group up the file names based off of their z position"""
uniquezs= np.unique(zPosArray)
groups = []
for i in range(len(uniquezs)):    
    indices = [j for j, x in enumerate(zPosArray) if x == uniquezs[i]]
    groups.append([fullnames[k] for k in indices])
    
"""from each group create an AVG, MIP, and minIP.  
flatten first across all images in a group first, then produce the 3 sets from that one """
rows = dp.Rows
columns = dp.Columns
avgset = np.empty((rows,columns, len(uniquezs)), dtype = np.int16)
minset = np.empty((rows,columns, len(uniquezs)), dtype = np.int16)
maxset = np.empty((rows,columns, len(uniquezs)), dtype = np.int16)
for i in range(len(uniquezs)):
    flatslice = np.empty((rows,columns, len(groups[i])) , dtype=np.int16)
    print("creating slice " + str(i+1))
    for j in range(len(groups[i])):  
        dp = pydicom.dcmread(groups[i][j])
        flatslice[:,:,j]=dp.pixel_array
        """now that the flat slice has been made, make the data """     
    for k in range(rows):        
        for l in range(columns):
            avgset[k,l,i] = sum(flatslice[k,l,:])/len(flatslice[k,l,:])
            minset[k,l,i] = min(flatslice[k,l,:])
            maxset[k,l,i] = max(flatslice[k,l,:])
            
    
""" now weve gotta write the sets back to dicom files""" 
avgseriesid = str(random.randint(0,1000000000000000000000000000000))
minseriesid = str(random.randint(0,1000000000000000000000000000000))
maxseriesid = str(random.randint(0,1000000000000000000000000000000))
os.chdir(mypath)
os.mkdir('new')
os.chdir(os.path.join(mypath, 'new'))
for i in range(len(uniquezs)):
    print("making file " + str(i+1))
    dp=pydicom.dcmread(groups[i][0])
    dp.PixelData = avgset[:,:,i].tobytes()
    dp.SeriesInstanceUID=avgseriesid
    dp.SeriesNumber = 84
    dp.SeriesDescription = "avg"
    savename = r"avg"+ str(i+1)+ ".dcm"
    dp.save_as(savename)
    dp=pydicom.dcmread(groups[i][1])
    dp.PixelData = minset[:,:,i].tobytes()
    dp.SeriesInstanceUID=minseriesid
    dp.SeriesNumber = 85
    dp.SeriesDescription = "min"
    savename = r"min"+ str(i+1)+ ".dcm"
    dp.save_as(savename)
    dp=pydicom.dcmread(groups[i][2])
    dp.PixelData = maxset[:,:,i].tobytes()
    dp.SeriesInstanceUID=maxseriesid
    dp.SeriesNumber = 86
    dp.SeriesDescription = "max"
    savename = r"max"+ str(i+1)+ ".dcm"
    dp.save_as(savename)
    
easygui.msgbox('Done!')
subprocess.Popen('explorer ' + os.path.dirname(savename))

