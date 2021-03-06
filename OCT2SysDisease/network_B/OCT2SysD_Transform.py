# OCT data transform class

import random
import torch
import math

class OCT2SysD_Transform(object):
    def __init__(self, hps):
        '''
        without random slice.
        '''
        super().__init__()
        self.hps = hps

    def __call__(self, inputData):
        '''

        :param inputData:  a Tensor of size(H,W),
        :return:
                a unnormalized tensor of size: H,W
        '''

        device = inputData.device

        data = inputData

        # random flip in each slice
        if random.uniform(0, 1) < self.hps.flipProb:
            data = torch.flip(data, [1])  # flip horizontal

        # gaussian noise
        if random.uniform(0, 1) < self.hps.augmentProb:
            data = data + torch.normal(0.0, self.hps.gaussianNoiseStd, size=data.size()).to(device=device,dtype=torch.float)

        # salt-pepper noise
        if random.uniform(0, 1) < self.hps.augmentProb:
            # salt: maxValue; pepper: minValue
            mask = torch.empty(data.size(),dtype=torch.float,device=device).uniform_(0,1)
            pepperMask = (mask <= self.hps.saltPepperRate)
            saltMask = (mask <= self.hps.saltPepperRate*self.hps.saltRate)
            pepperMask ^= saltMask  # xor
            max = data.max()
            min = data.min()
            data[torch.nonzero(pepperMask, as_tuple=True)] = min
            data[torch.nonzero(saltMask,   as_tuple=True)] = max

        return data

    def __repr__(self):
        return self.__class__.__name__

