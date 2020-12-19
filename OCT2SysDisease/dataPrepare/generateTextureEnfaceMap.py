# generate thickness en-face map

xmlDir = "/home/hxie1/data/BES_3K/W512NumpyVolumes/log/SurfacesNet/expBES3K_20201126A_genXml/testResult/xml"
volumeDir = "/home/hxie1/data/BES_3K/W512NumpyVolumes/volumes"
outputDir = "/home/hxie1/data/BES_3K/W512NumpyVolumes/log/SurfacesNet/expBES3K_20201126A_genXml/testResult/textureEnfaceMap"
# hPixelSize = 3.870

import glob
import numpy as np
import os
import sys
sys.path.append("../..")
from OCTMultiSurfaces.dataPrepare_Tongren.TongrenFileUtilities import getSurfacesArray

xmlVolumeList = glob.glob(xmlDir + f"/*_Volume_Sequence_Surfaces_Prediction.xml")
xmlVolumeList.sort()
nXmlVolumes = len(xmlVolumeList)
print(f"total {nXmlVolumes} volumes")

for xmlSegPath in xmlVolumeList:
    basename, ext = os.path.splitext(os.path.basename(xmlSegPath))
    volumeName = basename[0:basename.rfind("_Sequence_Surfaces_Prediction")]
    outputFilename = volumeName + f"_texture_enface" + ".npy"
    outputPath = os.path.join(outputDir, outputFilename)

    # read xml segmentation into array
    volumeSeg = getSurfacesArray(xmlSegPath).astype(np.int)  # BxNxW
    B,N,W = volumeSeg.shape

    # read raw volume
    volumePath = os.path.join(volumeDir, volumeName+".npy")
    volume = np.load(volumePath)  # BxHxW
    _, H, _ = volume.shape

    # define output empty array
    textureEnfaceVolume = np.empty((N - 1, B, W), dtype=np.float)
    # fill the output texture enface map
    for i in range(N - 1):
        surface0 = volumeSeg[:, i, :]  # BxW
        surface1 = volumeSeg[:, i + 1, :]  # BxW
        width = surface1 - surface0  # BxW # maybe 0
        for b in range(B):
            for w in range(W):
                if 0 == width[b, w]:
                    textureEnfaceVolume[i, b, w] = volume[b, surface0[b, w], w]
                elif width[b, w] >= 1:
                    textureEnfaceVolume[i, b, w] = volume[b, surface0[b, w]: surface1[b, w], w].sum() / width[b, w]  # BxW
                else:
                    print(f"Error: layer width is negative at b={b} and w={w} in {volumePath}")


    # output files
    np.save(outputPath, textureEnfaceVolume)

print(f"=======End of generating texture enface map==========")



