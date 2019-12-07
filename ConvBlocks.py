# Conv Block
import torch.nn as nn
import torch.nn.functional as F

class Conv3dBlock(nn.Module):
    """
    Convolution 3d Block
    """
    def __init__(self, inChannels, outChannels, convStride=1, useSpectralNorm=False, useLeakyReLU=False, kernelSize=3, padding=1):
        super().__init__()

        self.m_useLeakyReLU = useLeakyReLU

        self.m_conv = nn.Conv3d(inChannels, outChannels, kernel_size=kernelSize, stride=convStride, padding=padding, bias=True)
        if useSpectralNorm:
            self.m_conv = nn.utils.spectral_norm(self.m_conv)
        # self.m_norm = nn.BatchNorm3d(outChannels)
        self.m_norm = nn.InstanceNorm3d(outChannels)

    def forward(self, x):
        y = self.m_conv(x)

        # with Normalization
        y = F.relu(self.m_norm(y), inplace=True) if not self.m_useLeakyReLU \
            else F.leaky_relu(self.m_norm(y), inplace=True)

        # without Normalization
        # y = F.relu(y, inplace=True) if not self.m_useLeakyReLU \
        #     else F.leaky_relu(y, inplace=True)
        return y


class Conv2dBlock(nn.Module):
    """
    Convolution 2d Block
    """

    def __init__(self, inChannels, outChannels, convStride=1, useSpectralNorm=False,
                 useLeakyReLU=False, kernelSize=3, padding=1):
        super().__init__()

        self.m_useLeakyReLU = useLeakyReLU

        self.m_conv = nn.Conv2d(inChannels, outChannels, kernel_size=kernelSize, stride=convStride, padding=padding, bias=True)
        if useSpectralNorm:
            self.m_conv = nn.utils.spectral_norm(self.m_conv)
        # self.m_norm = nn.BatchNorm2d(outChannels)
        self.m_norm = nn.InstanceNorm2d(outChannels)

    def forward(self, x):
        y = self.m_conv(x)

        # with Normalization
        y = F.relu(self.m_norm(y), inplace=True) if not self.m_useLeakyReLU \
            else F.leaky_relu(self.m_norm(y), inplace=True)

        # without Normalization
        # y = F.relu(y, inplace=True) if not self.m_useLeakyReLU \
        #     else F.leaky_relu(y, inplace=True)

        return y

class LinearBlock(nn.Module):
    """
    Linear block
    """

    def __init__(self, inFeatures, outFeatures, useLeakyReLU=False, bias=True):
        super().__init__()

        self.m_useLeakyReLU = useLeakyReLU

        self.m_linear = nn.Linear(inFeatures, outFeatures, bias=bias)
        self.m_norm = nn.InstanceNorm2d(outFeatures)

    def forward(self, x):
        y = self.m_linear(x)

        # with Normalization
        y = F.relu(self.m_norm(y), inplace=True) if not self.m_useLeakyReLU \
            else F.leaky_relu(self.m_norm(y), inplace=True)

        return y

