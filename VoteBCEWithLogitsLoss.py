
from torch.nn.modules.loss import _Loss
import torch

class VoteBCEWithLogitsLoss(_Loss):
    def __init__(self, pos_weight=1):
        super().__init__()
        self.m_posWeight = pos_weight


    def forward(self, x, gts):
        B,F = x.shape
        BB,C = gts.shape
        assert B == BB and C==1
        sigmoidx = torch.sigmoid(x)
        gtsPlane = gts.expand((B,F))
        loss = -gtsPlane*torch.log(sigmoidx)*self.m_posWeight - (1.0-gtsPlane)*torch.log(1-sigmoidx)
        loss = loss.sum(dim=0)*1.0/B
        predictProb = sigmoidx.sum(dim=1)*1.0/F
        return predictProb, loss