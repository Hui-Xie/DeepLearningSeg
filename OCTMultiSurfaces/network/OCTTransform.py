# OCT data transform class

import random
import torch
import torchvision.transforms as TF

class OCTDataTransform(object):
    def __init__(self, prob=0, noiseStd=0.1, saltPepperRate=0.05, saltRate=0.5 ):
        self.m_prob = prob
        self.m_noiseStd = noiseStd
        self.m_saltPepperRate = saltPepperRate
        self.m_saltRate = saltRate

    def __call__(self, inputData):
        '''

        :param inputData:  a normalized Tensor of size(H,W),
        :return:
        '''
        H,W = inputData.shape
        device = inputData.device
        dirt =False
        data = inputData.clone()

        # gaussian noise
        if random.uniform(0, 1) < self.m_prob:
            data = data + torch.normal(0.0, self.m_noiseStd, size=data.size()).to(device)
            dirt = True

        # salt-pepper noise
        if random.uniform(0, 1) < self.m_prob:
            # salt: maxValue; pepper: minValue
            mask = torch.empty(data.size(),dtype=torch.float16,device=device).uniform_(0,1)
            pepperMask = mask <= self.m_saltPepperRate
            saltMask = mask <= self.m_saltPepperRate*self.m_saltRate
            pepperMask ^= saltMask
            max = data.max()
            min = data.min()
            data[torch.nonzero(pepperMask, as_tuple=True)] = min
            data[torch.nonzero(saltMask,   as_tuple=True)] = max
            dirt =True

        # normalize again
        if dirt:
            std, mean = torch.std_mean(data)
            data = TF.Normalize([mean], [std])(data.unsqueeze(dim=0))
            data = data.squeeze(dim=0)

        return data

    def __repr__(self):
        return self.__class__.__name__