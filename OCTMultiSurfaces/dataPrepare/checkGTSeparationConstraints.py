


segDir = "/home/hxie1/data/OCT_Beijing/Correcting_Seg"


# glob all file

import glob
import sys
sys.path.append(".")
from FileUtilities import *
import torch
import os


device = torch.device('cuda:1')
torch.set_printoptions(threshold=10000)

patientsList = glob.glob(segDir + f"/*_Volume_Sequence_Surfaces_Iowa.xml")
ouputFile = open(os.path.join(segDir, "violateSeparation.txt"), "w")


notes1 ="Check whether ground truth conforms the separation constraints: h_{i+1} >= h_i, where i is surface index.\n"
notes2 ="Only check 128:640 columns with column starting index 0 for each paitent and each OCT Bscan.\n"
notes3 ="In output below , column index w mean column (w+128) in original width 768 OCT images.\n"
notes4 ="In output below, bsan index starts with 0 which corresponds OCT1 in the original images.\n "

print(notes1, notes2,notes3, notes4, file=ouputFile)


errorPatients = 0
errorNum = 0
for patientXml in patientsList:
    surfacesArray = getSurfacesArray(patientXml)
    Z, Num_Surfaces, W = surfacesArray.shape
    assert Z == 31 and Num_Surfaces == 11 and W == 768
    surfacesArray = surfacesArray[:,:,128:640]
    surfaces = torch.from_numpy(surfacesArray).to(device)
    surface0 = surfaces[:,:-1,:]
    surface1 = surfaces[:,1:, :]
    if torch.all(surface1 >= surface0):
        continue
    else:
        errorPatients +=1
        patient = os.path.splitext(os.path.basename(patientXml))[0]
        errorLocations = torch.nonzero(surface0 > surface0)
        errorNum += errorLocations.shape[0]
        ouputFile.write(f"\n{patient} violates surface separation constraints in {errorLocations.shape[0]} locations indicated by below coordinates (BScan, surface, width):\n")
        print(errorLocations, file=ouputFile)

ouputFile.write(f"=============== {errorPatients} patients with total {errorNum} locations have ground truth not conforming separation constraints ============")
ouputFile.close()
print("end of program")



