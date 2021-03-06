# test Rift output

# need python package:  pillow(6.2.1), opencv, pytorch, torchvision, tensorboard

import sys
import random

import torch.optim as optim
from torch.utils import data
from torch.utils.tensorboard import SummaryWriter

sys.path.append("..")
from network.OCTDataSet import OCTDataSet
from network.OCTOptimization import *
from network.OCTTransform import *


sys.path.append(".")
from RiftSubnet import RiftSubnet
from ThicknessSubnet import ThicknessSubnet
from ThicknessSubnet_B import ThicknessSubnet_B
from ThicknessSubnet_C import ThicknessSubnet_C
from ThicknessSubnet_D import ThicknessSubnet_D
from ThicknessSubnet_E import ThicknessSubnet_E
from ThicknessSubnet_Y import ThicknessSubnet_Y
from ThicknessSubnet_Z1 import ThicknessSubnet_Z1
from ThicknessSubnet_Z2 import ThicknessSubnet_Z2
from ThicknessSubnet_Z3 import ThicknessSubnet_Z3
from ThicknessSubnet_Z4 import ThicknessSubnet_Z4

import time
import numpy as np
import datetime

sys.path.append("../..")
from utilities.FilesUtilities import *
from utilities.TensorUtilities import *
from framework.NetMgr import NetMgr
from framework.ConfigReader import ConfigReader
from framework.NetTools import *


def printUsage(argv):
    print("============ Cross Validation Test OCT MultiSurface Network =============")
    print("Usage:")
    print(argv[0], " yaml_Config_file_path")

def main():

    if len(sys.argv) != 2:
        print("Error: input parameters error.")
        printUsage(sys.argv)
        return -1

    # parse config file
    configFile = sys.argv[1]
    hps = ConfigReader(configFile)
    print(f"Experiment: {hps.experimentName}")

    if hps.dataIn1Parcel:
        if -1 == hps.k and 0 == hps.K:  # do not use cross validation
            testImagesPath = os.path.join(hps.dataDir, "test", f"images.npy")
            testLabelsPath = os.path.join(hps.dataDir, "test", f"surfaces.npy") if hps.existGTLabel else None
            testIDPath = os.path.join(hps.dataDir, "test", f"patientID.json")
        else:  # use cross validation
            testImagesPath = os.path.join(hps.dataDir, "test", f"images_CV{hps.k:d}.npy")
            testLabelsPath = os.path.join(hps.dataDir, "test", f"surfaces_CV{hps.k:d}.npy")
            testIDPath = os.path.join(hps.dataDir, "test", f"patientID_CV{hps.k:d}.json")
    else:
        if -1 == hps.k and 0 == hps.K:  # do not use cross validation
            testImagesPath = os.path.join(hps.dataDir, "test", f"patientList.txt")
            testLabelsPath = None
            testIDPath = None
        else:
            print(f"Current do not support Cross Validation and not dataIn1Parcel\n")
            assert (False)

    testData = OCTDataSet(testImagesPath, testIDPath, testLabelsPath,  transform=None, hps=hps)

    # construct network
    net = eval(hps.network)(hps=hps)
    # Important:
    # If you need to move a model to GPU via .cuda(), please do so before constructing optimizers for it.
    # Parameters of a model after .cuda() will be different objects with those before the call.
    net.to(device=hps.device)

    # Load network
    netMgr = NetMgr(net, hps.netPath, hps.device)
    netMgr.loadNet("test")

    # test
    testStartTime = time.time()
    net.eval()
    with torch.no_grad():
        testBatch = 0
        net.setStatus("test")
        net.m_epoch = net.m_runParametersDict['epoch']
        for batchData in data.DataLoader(testData, batch_size=hps.batchSize, shuffle=False, num_workers=0):
            testBatch += 1
            R, loss = net.forward(batchData['images'], gaussianGTs=batchData['gaussianGTs'], GTs=batchData['GTs'],
                                        layerGTs=batchData['layers'], riftGTs=batchData['riftWidth'])
            batchImages = batchData['images'][:, 0, :, :]  # erase grad channels to save memory
            # images = torch.cat((images, batchImages)) if testBatch != 1 else batchImages  # for output result
            if hps.existGTLabel:
                testGts = torch.cat((testGts, batchData['riftWidth'])) if testBatch != 1 else batchData['riftWidth']
            else:
                testGts = None

            testIDs = testIDs + batchData['IDs'] if testBatch != 1 else batchData['IDs']  # for future output predict images

            testR = torch.cat((testR, R)) if testBatch != 1 else R


        if hps.existGTLabel:
            goodBScansInGtOrder = None
            stdSurfaceError, muSurfaceError, stdError, muError = computeErrorStdMuOverPatientDimMean(testR,
                                                                                                     testGts,
                                                                                                     slicesPerPatient=hps.slicesPerPatient,
                                                                                                     hPixelSize=hps.hPixelSize,
                                                                                                     goodBScansInGtOrder=goodBScansInGtOrder)
            testGts = testGts.cpu().numpy()
            testGtsFilePath = os.path.join(hps.outputDir, f"testRiftGts.npy")
            np.save(testGtsFilePath, testGts)

        testR = testR.cpu().numpy()
        if hps.existGTLabel:
            hausdorffD = columnHausdorffDist(testR, testGts).reshape(1, -1)

        testRFilePath = os.path.join(hps.outputDir, f"testR.npy")
        np.save(testRFilePath, testR)

        # output testID
        with open(os.path.join(hps.outputDir, f"testID.txt"), "w") as file:
            for id in testIDs:
                file.write(f"{id}\n")

        #images = images.cpu().numpy().squeeze()
        

    testEndTime = time.time()
    B,S,W = testR.shape
    # _,H,_ = images.shape

    # final output result:
    curTime = datetime.datetime.now()
    timeStr = f"{curTime.year}{curTime.month:02d}{curTime.day:02d}_{curTime.hour:02d}{curTime.minute:02d}{curTime.second:02d}"

    with open(os.path.join(hps.outputDir, f"output_{timeStr}.txt"), "w") as file:
        hps.printTo(file)
        file.write("\n=======net running parameters=========\n")
        file.write(f"B,S,H,W = {B, S, hps.inputHeight, W}\n")
        file.write(f"Test time: {testEndTime - testStartTime} seconds.\n")
        file.write(f"net.m_runParametersDict:\n")
        [file.write(f"\t{key}:{value}\n") for key, value in net.m_runParametersDict.items()]

        file.write(f"\n\n===============Formal Output Result ===========\n")
        if hps.existGTLabel:
            file.write(f"stdThicknessError = {stdSurfaceError}\n")
            file.write(f"muThicknessError = {muSurfaceError}\n")
            file.write(f"stdError = {stdError}\n")
            file.write(f"muError = {muError}\n")
            file.write(f"hausdorff distance(pixel) of Thickness = {hausdorffD}\n")



    print(f"============ End of Cross valiation test for OCT Multisurface Network: {hps.experimentName} ===========")




if __name__ == "__main__":
    main()
