# Base on SurfacesUnet_YufanHe_2 nework, the exact YufanHe network
# to deduce (N-1) thickness from N surface.


import sys
import math

sys.path.append(".")
sys.path.append("../..")
from network.OCTOptimization import *
from network.OCTAugmentation import *
import torch

sys.path.append("../..")
from framework.NetTools import *
from framework.BasicModel import BasicModel
from framework.ConvBlocks import *
from framework.CustomizedLoss import  GeneralizedDiceLoss, MultiSurfaceCrossEntropyLoss, SmoothSurfaceLoss, logits2Prob, MultiLayerCrossEntropyLoss, SmoothThicknessLoss

class ThicknessSubnet_E(BasicModel):  #
    ''''
    This network refer Yufan He paper: He,Y., Carass A., Liu, Yi., et al. (2019).:
    Fully Convolutional Boundary Regression for Retina OCT Segmentation.
    In: Medical Image Computing and Computer Assisted Intervention(MICCAI 2019).
    \doi{10.1007/978-3-030-32239-7\_14}
    '''
    def __init__(self, hps=None):
        '''
        inputSize: inputChaneels*H*W
        outputSize: (Surface, H, W)
        :param numSurfaces:
        :param N: startFilters
        '''
        super().__init__()
        self.hps = hps

        self.m_inputHeight = hps.inputHeight
        self.m_inputWidth = hps.inputWidth
        self.m_inputChannels = hps.inputChannels
        self.m_nLayers = hps.nLayers
        self.m_layerSizeList = computeLayerSizeUsingMaxPool2D(self.m_inputHeight, self.m_inputWidth, self.m_nLayers)
        N = hps.startFilters

        self.m_useSpectralNorm = False
        self.m_useLeakyReLU = True
        # downxPooling layer is responsible change size of feature map (by MaxPool) and number of filters.
        self.m_down0Pooling = nn.Sequential(
            Conv2dBlock(self.m_inputChannels, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )
        self.m_down0 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down1Pooling = nn.Sequential(
            nn.MaxPool2d(2, stride=2, padding=0)
        )
        self.m_down1 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
            )

        self.m_down2Pooling = nn.Sequential(
            nn.MaxPool2d(2, stride=2, padding=0)
        )
        self.m_down2 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
            )

        self.m_down3Pooling = nn.Sequential(
            nn.MaxPool2d(2, stride=2, padding=0)
        )
        self.m_down3 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down4Pooling = nn.Sequential(
            nn.MaxPool2d(2, stride=2, padding=0)
        )

        self.m_down4 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        # this is the bottleNeck at bottom with size: self.m_layerSizeList[6]
        self.m_up4Pooling = nn.Upsample(size=self.m_layerSizeList[3], mode='bilinear')
        self.m_up4AfterCat= Conv2dBlock(N*2, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        self.m_up4 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up3Pooling = nn.Upsample(size=self.m_layerSizeList[2], mode='bilinear')
        self.m_up3AfterCat= Conv2dBlock(N*2, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        self.m_up3 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up2Pooling = nn.Upsample(size=self.m_layerSizeList[1], mode='bilinear')
        self.m_up2AfterCat = Conv2dBlock(N*2,  N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        self.m_up2 = nn.Sequential(
            Conv2dBlock(N , N, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up1Pooling = nn.Upsample(size=self.m_layerSizeList[0], mode='bilinear')
        self.m_up1AfterCat = Conv2dBlock(N*2, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)

        self.m_up1 = nn.Sequential(
            Conv2dBlock(N, N, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(N, N, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        # 2 branches:
        self.m_surfaces = nn.Sequential(
            Conv2dBlock(N, N//2, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            nn.Conv2d(N//2, hps.numSurfaces, kernel_size=1, stride=1, padding=0)  # conv 1*1
        )  # output size:numSurfaces*H*W

        self.m_layers = nn.Sequential(
            Conv2dBlock(N, N//2, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            nn.Conv2d(N//2, hps.numSurfaces + 1, kernel_size=1, stride=1, padding=0)  # conv 1*1
        )  # output size:(numSurfaces+1)*H*W


    def forward(self, inputs, gaussianGTs=None, GTs=None, layerGTs=None, riftGTs=None):
        # compute outputs
        device = inputs.device

        x0 = self.m_down0Pooling(inputs)
        x0 = self.m_down0(x0) + x0    # this residual link may hurts dice performance.
        x0 = self.m_down0(x0)

        x1 = self.m_down1Pooling(x0)
        x1 = self.m_down1(x1) + x1

        x2 = self.m_down2Pooling(x1)
        x2 = self.m_down2(x2) + x2

        x3 = self.m_down3Pooling(x2)
        x3 = self.m_down3(x3) + x3

        x4 = self.m_down4Pooling(x3)
        x4 = self.m_down4(x4) + x4

        x = x4 # bottom

        x = torch.cat((self.m_up4Pooling(x), x3), dim=1)
        x = self.m_up4AfterCat(x)
        x = self.m_up4(x) + x

        x = torch.cat((self.m_up3Pooling(x), x2), dim=1)
        x = self.m_up3AfterCat(x)
        x = self.m_up3(x) + x

        x = torch.cat((self.m_up2Pooling(x), x1), dim=1)
        x = self.m_up2AfterCat(x)
        x = self.m_up2(x) + x

        x = torch.cat((self.m_up1Pooling(x), x0), dim=1)
        x = self.m_up1AfterCat(x)
        x = self.m_up1(x) + x

        xs = self.m_surfaces(x)  # xs means x_surfaces, # output size: B*numSurfaces*H*W
        xl = self.m_layers(x)  # xs means x_layers,   # output size: B*(numSurfaces+1)*H*W


        B,N,H,W = xs.shape

        hps = self.hps

        layerMu = None # referred surface mu computed by layer segmentation.
        layerConf = None
        surfaceProb = logits2Prob(xs, dim=-2)
        layerProb = logits2Prob(xl, dim=1)

        loss_layer = 0.0
        if hps.useLayerDice:
            generalizedDiceLoss = GeneralizedDiceLoss()
            loss_layer = generalizedDiceLoss(layerProb, layerGTs)
            # layerMu, layerConf = layerProb2SurfaceMu(layerProb)  # use layer segmentation to refer surface mu.

            # add layer CE loss
            multiLayerCE = MultiLayerCrossEntropyLoss()
            loss_layer += multiLayerCE(layerProb, layerGTs)

        mu, sigma2 = computeMuVariance(surfaceProb, layerMu=layerMu, layerConf=layerConf)

        multiSurfaceCE = MultiSurfaceCrossEntropyLoss()
        loss_surfaceCE = multiSurfaceCE(surfaceProb, GTs)  # CrossEntropy is a kind of KLDiv


        #ReLU to guarantee layer order
        S = mu.clone()
        for i in range(1,N):
            S[:,i,:] = torch.where(S[:, i,:]< S[:,i-1,:], S[:,i-1,:], S[:,i,:])
        thickness = S[:, 1:, :] - S[:, 0:-1, :]  # size: B,N-1,W
        R = thickness

        # use smoothLoss and L1loss for surface and rift
        loss_surfaceL1 = 0.0
        loss_surfaceSmooth = 0.0
        loss_riftL1 = 0.0
        loss_riftSmooth = 0.0
        if self.hps.existGTLabel:
            if self.hps.useL1Loss:
                surfaceL1Loss = nn.SmoothL1Loss().to(device)
                loss_surfaceL1 = surfaceL1Loss(S, GTs)

                riftL1Loss = nn.SmoothL1Loss().to(device)
                loss_riftL1 = riftL1Loss(R, riftGTs)

            if self.hps.useSmoothSurfaceLoss:
                smoothSurfaceLoss = SmoothSurfaceLoss(mseLossWeight=5.0)
                loss_surfaceSmooth = smoothSurfaceLoss(S, GTs)

            if self.hps.useSmoothThicknessLoss:
                smoothThicknessLoss = SmoothThicknessLoss(mseLossWeight=5.0)
                loss_riftSmooth = smoothThicknessLoss(R, riftGTs)

        loss = loss_layer + loss_surfaceCE + loss_surfaceL1 +loss_surfaceSmooth+ loss_riftL1 + loss_riftSmooth

        if torch.isnan(loss.sum()):  # detect NaN
            print(f"Error: find NaN loss at epoch {self.m_epoch}")
            assert False

        return thickness, loss  # return rift R in (B,N-1,W) dimension and loss



