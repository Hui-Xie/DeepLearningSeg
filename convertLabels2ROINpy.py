
import os
import SimpleITK as sitk
from scipy import ndimage
import numpy as np
from DataMgr import DataMgr

suffix = "_Seg.nrrd"
inputsDir = "/home/hxie1/data/OvarianCancerCT/Extract_uniform/testLabels"
outputsDir = "/home/hxie1/data/OvarianCancerCT/Extract_uniform/testLabels_ROI_147_281_281"
readmeFile = "/home/hxie1/data/OvarianCancerCT/Extract_uniform/testLabels_ROI_147_281_281/readme.txt"

# inputsDir = "/home/hxie1/data/OvarianCancerCT/Extract_uniform/trainLabels"
# outputsDir = "/home/hxie1/data/OvarianCancerCT/Extract_uniform/trainLabels_ROI_147_281_281"
# readmeFile = "/home/hxie1/data/OvarianCancerCT/Extract_uniform/trainLabels_ROI_147_281_281/readme.txt"

goalSize = (147,281,281)

originalCwd = os.getcwd()
os.chdir(inputsDir)
filesList = [os.path.abspath(x) for x in os.listdir(inputsDir) if suffix in x]
os.chdir(originalCwd)

dataMgr = DataMgr("", "", suffix)
dataMgr.setDataSize(0, goalSize[0], goalSize[1],goalSize[2], 0, "ConvertNrrd2ROI")
radius = goalSize[0]//2

for file in filesList:
    label3d = sitk.GetArrayFromImage(sitk.ReadImage(file))

    label3dB = (label3d > 0)  # label3D binary version
    massCenterFloat = ndimage.measurements.center_of_mass(label3dB)
    massCenter = []
    for i in range(len(massCenterFloat)):
        massCenter.append(int(massCenterFloat[i]))

    roi = dataMgr.cropVolumeCopy(label3d, massCenter[0], massCenter[1],  massCenter[2], radius)

    # erase label 3(lymph node)
    roi3 = roi >=3
    roi[np.nonzero(roi3)] = 0

    patientID = DataMgr.getStemName(file, suffix)
    np.save(os.path.join(outputsDir, patientID + "_roi.npy"), roi)

N = len(filesList)

with open(readmeFile,"w") as f:
    f.write(f"total {N} files in this directory\n")
    f.write(f"all output numpy array have erased label>=3")
    f.write(f"goalSize: {goalSize}\n")
    f.write(f"inputsDir = {inputsDir}\n")
