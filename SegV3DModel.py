import torch
import torch.nn as nn
import torch.nn.functional as F

from BasicModel import BasicModel
from ConvBlocks import *


#  3D model

class SegV3DModel(BasicModel):
    def __init__(self):  # K is the final output classification number.
        super().__init__()

        # For input image size: 49*147*147 (zyx in nrrd format)
        # at Oct 5th, 2019, Saturday
        #
        self.m_useSpectralNorm = True
        self.m_useLeakyReLU = True
        self.m_down0 = nn.Sequential(
            Conv3dBlock(1, 48, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(48, 48, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(48, 48, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 48*49*147*147

        self.m_down1Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(48, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 64*24*73*73
        self.m_down1 = nn.Sequential(
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down2Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(64, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 128*11*36*36
        self.m_down2 = nn.Sequential(
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down3Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(128, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 256*5*17*17
        self.m_down3 = nn.Sequential(
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down4Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(256, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 512*2*8*8
        self.m_down4 = nn.Sequential(
            Conv3dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down5Pooling = nn.Sequential(
            nn.AvgPool3d((2, 3, 3), stride=2, padding=0)
        )  # outputSize:512*1*3*3, followed squeeze
        self.m_down5 = nn.Sequential(
            Conv2dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        # here needs unsqueeze at dim 1

        self.m_up5Pooling = nn.Sequential(
            nn.Upsample(size=(2, 8, 8), mode='trilinear')  # ouput size: 512*2*8*8
        )
        self.m_up5 = nn.Sequential(
            Conv3dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up4Pooling = nn.Sequential(
            nn.Upsample(size=(5, 17, 17), mode='trilinear'),
            Conv3dBlock(512, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 256*5*17*17
        self.m_up4 = nn.Sequential(
            Conv3dBlock(256, 256, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up3Pooling = nn.Sequential(
            nn.Upsample(size=(11, 36, 36), mode='trilinear'),
            Conv3dBlock(256, 128, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 128*11*36*36
        self.m_up3 = nn.Sequential(
            Conv3dBlock(128, 128, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up2Pooling = nn.Sequential(
            nn.Upsample(size=(24, 73, 73), mode='trilinear'),
            Conv3dBlock(128, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 64*24*73*73
        self.m_up2 = nn.Sequential(
            Conv3dBlock(64, 64, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up1Pooling = nn.Sequential(
            nn.Upsample(size=(49, 147, 147), mode='trilinear'),
            Conv3dBlock(64, 48, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 48*49*147*147
        self.m_up1 = nn.Sequential(
            Conv3dBlock(48, 48, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(48, 48, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(48, 48, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up0 = nn.Sequential(
            nn.Conv3d(48, 2, kernel_size=3, stride=1, padding=1)
        )  # output size:2*49*147*147

        '''
        # For input image size: 51*149*149 (zyx in nrrd format)
        # at Sep30th, 2019
        #
        self.m_useSpectralNorm = True
        self.m_useLeakyReLU = True
        self.m_down0 = nn.Sequential(
            Conv3dBlock(1, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 32*51*149*149

        self.m_down1Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(32, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 64*25*74*74
        self.m_down1 = nn.Sequential(
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down2Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(64, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 128*12*36*36
        self.m_down2 = nn.Sequential(
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down3Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(128, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 256*5*17*17
        self.m_down3 = nn.Sequential(
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down4Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(256, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 512*2*8*8
        self.m_down4 = nn.Sequential(
            Conv3dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down5Pooling = nn.Sequential(
            nn.AvgPool3d((2, 3, 3), stride=2, padding=0)
        )  # outputSize:512*1*3*3, followed squeeze
        self.m_down5 = nn.Sequential(
            Conv2dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        # here needs unsqueeze at dim 1

        self.m_up5Pooling = nn.Sequential(
            nn.Upsample(size=(2, 8, 8), mode='trilinear')  # ouput size: 512*2*8*8
        )
        self.m_up5 = nn.Sequential(
            Conv3dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up4Pooling = nn.Sequential(
            nn.Upsample(size=(5, 17, 17), mode='trilinear'),
            Conv3dBlock(512, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 256*5*17*17
        self.m_up4 = nn.Sequential(
            Conv3dBlock(256, 256, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up3Pooling = nn.Sequential(
            nn.Upsample(size=(12, 36, 36), mode='trilinear'),
            Conv3dBlock(256, 128, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 128*12*36*36
        self.m_up3 = nn.Sequential(
            Conv3dBlock(128, 128, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up2Pooling = nn.Sequential(
            nn.Upsample(size=(25, 74, 74), mode='trilinear'),
            Conv3dBlock(128, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 64*25*74*74
        self.m_up2 = nn.Sequential(
            Conv3dBlock(64, 64, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up1Pooling = nn.Sequential(
            nn.Upsample(size=(51, 149, 149), mode='trilinear'),
            Conv3dBlock(64, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 32*51*149*149
        self.m_up1 = nn.Sequential(
            Conv3dBlock(32, 32, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up0 = nn.Sequential(
            nn.Conv3d(32, 2, kernel_size=3, stride=1, padding=1)
        )  # output size:2*51*149*149
        
        '''



        '''
        # For input image size: 51*171*171 (zyx in nrrd format)
        # at Sep 14, 2019-Sep30th, 2019
        #
        self.m_useSpectralNorm = True
        self.m_useLeakyReLU = True
        self.m_down0 = nn.Sequential(
            Conv3dBlock(1, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 32*51*171*171

        self.m_down1Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(32, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 64*25*85*85
        self.m_down1 = nn.Sequential(
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down2Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(64, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 128*12*42*42
        self.m_down2 = nn.Sequential(
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down3Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(128, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 256*5*20*20
        self.m_down3 = nn.Sequential(
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down4Pooling = nn.Sequential(
            nn.AvgPool3d(3, stride=2, padding=0),
            Conv3dBlock(256, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 512*2*9*9
        self.m_down4 = nn.Sequential(
            Conv3dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_down5Pooling = nn.Sequential(
            nn.AvgPool3d((2, 3, 3), stride=2, padding=0)  # outputSize:512*1*4*4, followed squeeze
        )
        self.m_down5 = nn.Sequential(
            Conv2dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv2dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        # here needs unsqueeze at dim 1

        self.m_up5Pooling = nn.Sequential(
            nn.Upsample(size=(2, 9, 9), mode='trilinear')  # ouput size: 512*2*9*9
        )
        self.m_up5 = nn.Sequential(
            Conv3dBlock(512, 512, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(512, 512, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up4Pooling = nn.Sequential(
            nn.Upsample(size=(5, 20, 20), mode='trilinear'),
            Conv3dBlock(512, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 256*5*20*20
        self.m_up4 = nn.Sequential(
            Conv3dBlock(256, 256, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(256, 256, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up3Pooling = nn.Sequential(
            nn.Upsample(size=(12, 42, 42), mode='trilinear'),
            Conv3dBlock(256, 128, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 128*12*42*42
        self.m_up3 = nn.Sequential(
            Conv3dBlock(128, 128, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(128, 128, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up2Pooling = nn.Sequential(
            nn.Upsample(size=(25, 85, 85), mode='trilinear'),
            Conv3dBlock(128, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
        )  # ouput size: 64*25*85*85
        self.m_up2 = nn.Sequential(
            Conv3dBlock(64, 64, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(64, 64, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up1Pooling = nn.Sequential(
            nn.Upsample(size=(51, 171, 171), mode='trilinear'),
            Conv3dBlock(64, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU)
        )  # ouput size: 32*51*171*171
        self.m_up1 = nn.Sequential(
            Conv3dBlock(32, 32, convStride=1,
                        useSpectralNorm=self.m_useSpectralNorm, useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU),
            Conv3dBlock(32, 32, convStride=1, useSpectralNorm=self.m_useSpectralNorm,
                        useLeakyReLU=self.m_useLeakyReLU)
        )

        self.m_up0 = nn.Sequential(
            nn.Conv3d(32, 2, kernel_size=3, stride=1, padding=1)
        )  # output size:2*51*171*171
        
        '''



    def forward(self, x, gts):
        # compute outputs
        x0 = self.m_down0(x)

        x1 = self.m_down1Pooling(x0)
        x1 = self.m_down1(x1) + x1

        x2 = self.m_down2Pooling(x1)
        x2 = self.m_down2(x2) + x2

        x3 = self.m_down3Pooling(x2)
        x3 = self.m_down3(x3) + x3

        x4 = self.m_down4Pooling(x3)
        x4 = self.m_down4(x4) + x4

        x5 = self.m_down5Pooling(x4)
        x5 = torch.squeeze(x5, dim=2)
        x5 = self.m_down5(x5) + x5  # bottom neck output

        x = torch.unsqueeze(x5, dim=2)
        x = self.m_up5Pooling(x) + x4
        x = self.m_up5(x) + x

        x = self.m_up4Pooling(x) + x3
        x = self.m_up4(x) + x

        x = self.m_up3Pooling(x) + x2
        x = self.m_up3(x) + x

        x = self.m_up2Pooling(x) + x1
        x = self.m_up2(x) + x

        x = self.m_up1Pooling(x) + x0
        x = self.m_up1(x) + x

        outputs = self.m_up0(x)

        # compute loss (put loss here is to save main GPU memory)
        loss = torch.tensor(0.0).to(x.device)
        for lossFunc, weight in zip(self.m_lossFuncList, self.m_lossWeightList):
            if weight == 0:
                continue
            lossFunc.to(x.device)
            loss += lossFunc(outputs, gts) * weight

        return outputs, loss
