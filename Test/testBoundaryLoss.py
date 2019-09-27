import sys
import numpy as np
sys.path.append("..")
from CustomizedLoss import *
import torch.nn as nn

import torch

inputs = torch.tensor([
                   [ [[0,0,0,0,0], [0,0,0,0,0], [0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
                     [[0,0,0,0,0], [0,2,2,2,0], [0,2,2,2,0],[0,0,0,0,0],[0,0,0,0,0]]],
                   [ [[0,0,0,0,0], [0,0,0,0,0], [0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
                     [[0,0,0,0,0], [0,0,0,0,0], [0,0,0,0,0],[1,1,0,0,0],[1,1,0,0,0]]] ], dtype=torch.float32, requires_grad=True)

targets = torch.tensor([
                   [[0,1,1,1,0], [0,1,1,1,0], [0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
                   [[0,0,0,1,1], [0,0,0,1,1], [0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]] ])



# lossFunc = BoundaryLoss3(weight=torch.tensor([1.0, 4.0]))
# lossFunc = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 4.0]))
# lossFunc = FullCrossEntropyLoss(weight=torch.tensor([1.0, 4.0]))
lossFunc = DistanceCrossEntropyLoss(weight=torch.tensor([1.0, 4.0]))

inputs= inputs.cuda()

lossFun.cuda()
loss = lossFunc(inputs, targets)


print (f"Loss = {loss.item()}")

inputs.retain_grad() # Enables .grad attribute for non-leaf Tensors.
loss.backward()

print (f"inputs gradient = {inputs.grad}")


'''
Experiment result:
A  When BoundaryLoss3 is -logP * levelSetFgTensor - log1_P*levelSetBgTensor:
1   gradient on P and (1-P) are almost symmetric, e.g gradient p= 0.0620, while graident on(1-p) = -0.0620;
2   Farther distance, bigger gradient absolute value; 

Loss = 1.5893921852111816
inputs gradient = tensor(
       [[[[-0.0100,  0.0100,  0.0200,  0.0100, -0.0100],
          [-0.0100,  0.0024,  0.0024,  0.0024, -0.0100],
          [-0.0141, -0.0176, -0.0176, -0.0176, -0.0141],
          [-0.0224, -0.0200, -0.0200, -0.0200, -0.0224],
          [-0.0316, -0.0300, -0.0300, -0.0300, -0.0316]],

         [[ 0.0100, -0.0100, -0.0200, -0.0100,  0.0100],
          [ 0.0100, -0.0024, -0.0024, -0.0024,  0.0100],
          [ 0.0141,  0.0176,  0.0176,  0.0176,  0.0141],
          [ 0.0224,  0.0200,  0.0200,  0.0200,  0.0224],
          [ 0.0316,  0.0300,  0.0300,  0.0300,  0.0316]]],


        [[[-0.0300, -0.0200, -0.0100,  0.0100,  0.0200],
          [-0.0300, -0.0200, -0.0100,  0.0100,  0.0100],
          [-0.0316, -0.0224, -0.0141, -0.0100, -0.0100],
          [-0.0527, -0.0414, -0.0224, -0.0200, -0.0200],
          [-0.0620, -0.0527, -0.0316, -0.0300, -0.0300]],

         [[ 0.0300,  0.0200,  0.0100, -0.0100, -0.0200],
          [ 0.0300,  0.0200,  0.0100, -0.0100, -0.0100],
          [ 0.0316,  0.0224,  0.0141,  0.0100,  0.0100],
          [ 0.0527,  0.0414,  0.0224,  0.0200,  0.0200],
          [ 0.0620,  0.0527,  0.0316,  0.0300,  0.0300]]]], device='cuda:0')



B   When BoundaryLoss3 is -(logP-log1_P) * (levelSetFgTensor - levelSetBgTensor):
1  gradient on P and (1-P) are almost symmetric, e.g gradient p= 0.0849, while graident on(1-p) = -0.0849;
2  the graident absolute value increase, comparing with experiment1;  It is stronger gradient signals to improve.
3  Farther distance, bigger gradient absolute value; 
 
Loss = 0.2856433689594269
inputs gradient = tensor(
       [[[[-0.0200,  0.0200,  0.0400,  0.0200, -0.0200],
          [-0.0200,  0.0200,  0.0200,  0.0200, -0.0200],
          [-0.0283, -0.0200, -0.0200, -0.0200, -0.0283],
          [-0.0447, -0.0400, -0.0400, -0.0400, -0.0447],
          [-0.0632, -0.0600, -0.0600, -0.0600, -0.0632]],

         [[ 0.0200, -0.0200, -0.0400, -0.0200,  0.0200],
          [ 0.0200, -0.0200, -0.0200, -0.0200,  0.0200],
          [ 0.0283,  0.0200,  0.0200,  0.0200,  0.0283],
          [ 0.0447,  0.0400,  0.0400,  0.0400,  0.0447],
          [ 0.0632,  0.0600,  0.0600,  0.0600,  0.0632]]],


        [[[-0.0600, -0.0400, -0.0200,  0.0200,  0.0400],
          [-0.0600, -0.0400, -0.0200,  0.0200,  0.0200],
          [-0.0632, -0.0447, -0.0283, -0.0200, -0.0200],
          [-0.0721, -0.0566, -0.0447, -0.0400, -0.0400],
          [-0.0849, -0.0721, -0.0632, -0.0600, -0.0600]],

         [[ 0.0600,  0.0400,  0.0200, -0.0200, -0.0400],
          [ 0.0600,  0.0400,  0.0200, -0.0200, -0.0200],
          [ 0.0632,  0.0447,  0.0283,  0.0200,  0.0200],
          [ 0.0721,  0.0566,  0.0447,  0.0400,  0.0400],
          [ 0.0849,  0.0721,  0.0632,  0.0600,  0.0600]]]], device='cuda:0')

Experiment 3:
C   use unbalanded weight [1.0, 4.0] with boundaryLoss3: -logP *self.weight[k]* levelSetFgTensor - log1_P*levelSetBgTensor,
Loss = 1.9865388870239258
inputs gradient = tensor([[[[-0.0100,  0.0400,  0.0800,  0.0400, -0.0100],
          [-0.0100,  0.0095,  0.0095,  0.0095, -0.0100],
          [-0.0141, -0.0176, -0.0176, -0.0176, -0.0141],
          [-0.0224, -0.0200, -0.0200, -0.0200, -0.0224],
          [-0.0316, -0.0300, -0.0300, -0.0300, -0.0316]],

         [[ 0.0100, -0.0400, -0.0800, -0.0400,  0.0100],
          [ 0.0100, -0.0095, -0.0095, -0.0095,  0.0100],
          [ 0.0141,  0.0176,  0.0176,  0.0176,  0.0141],
          [ 0.0224,  0.0200,  0.0200,  0.0200,  0.0224],
          [ 0.0316,  0.0300,  0.0300,  0.0300,  0.0316]]],


        [[[-0.0300, -0.0200, -0.0100,  0.0400,  0.0800],
          [-0.0300, -0.0200, -0.0100,  0.0400,  0.0400],
          [-0.0316, -0.0224, -0.0141, -0.0100, -0.0100],
          [-0.0527, -0.0414, -0.0224, -0.0200, -0.0200],
          [-0.0620, -0.0527, -0.0316, -0.0300, -0.0300]],

         [[ 0.0300,  0.0200,  0.0100, -0.0400, -0.0800],
          [ 0.0300,  0.0200,  0.0100, -0.0400, -0.0400],
          [ 0.0316,  0.0224,  0.0141,  0.0100,  0.0100],
          [ 0.0527,  0.0414,  0.0224,  0.0200,  0.0200],
          [ 0.0620,  0.0527,  0.0316,  0.0300,  0.0300]]]], device='cuda:0')





Experiement4:
C   use unbalanded weight [1.0, 4.0] with boundaryLoss3: -(logP*self.weight[k]-log1_P) * (levelSetFgTensor - levelSetBgTensor)
Loss = -2.4713101387023926
inputs gradient = tensor(
       [[[[-0.0500,  0.0500,  0.1000,  0.0500, -0.0500],
          [-0.0500,  0.0272,  0.0272,  0.0272, -0.0500],
          [-0.0707, -0.0272, -0.0272, -0.0272, -0.0707],
          [-0.1118, -0.1000, -0.1000, -0.1000, -0.1118],
          [-0.1581, -0.1500, -0.1500, -0.1500, -0.1581]],

         [[ 0.0500, -0.0500, -0.1000, -0.0500,  0.0500],
          [ 0.0500, -0.0272, -0.0272, -0.0272,  0.0500],
          [ 0.0707,  0.0272,  0.0272,  0.0272,  0.0707],
          [ 0.1118,  0.1000,  0.1000,  0.1000,  0.1118],
          [ 0.1581,  0.1500,  0.1500,  0.1500,  0.1581]]],


        [[[-0.1500, -0.1000, -0.0500,  0.0500,  0.1000],
          [-0.1500, -0.1000, -0.0500,  0.0500,  0.0500],
          [-0.1581, -0.1118, -0.0707, -0.0500, -0.0500],
          [-0.1303, -0.1022, -0.1118, -0.1000, -0.1000],
          [-0.1533, -0.1303, -0.1581, -0.1500, -0.1500]],

         [[ 0.1500,  0.1000,  0.0500, -0.0500, -0.1000],
          [ 0.1500,  0.1000,  0.0500, -0.0500, -0.0500],
          [ 0.1581,  0.1118,  0.0707,  0.0500,  0.0500],
          [ 0.1303,  0.1022,  0.1118,  0.1000,  0.1000],
          [ 0.1533,  0.1303,  0.1581,  0.1500,  0.1500]]]], device='cuda:0')


Experiment5 : use std CrossEntropyLoss with weight
Loss = 0.6929869651794434
inputs gradient = tensor([[[[-0.0063,  0.0250,  0.0250,  0.0250, -0.0063],
          [-0.0063,  0.0060,  0.0060,  0.0060, -0.0063],
          [-0.0063, -0.0110, -0.0110, -0.0110, -0.0063],
          [-0.0063, -0.0063, -0.0063, -0.0063, -0.0063],
          [-0.0063, -0.0063, -0.0063, -0.0063, -0.0063]],

         [[ 0.0063, -0.0250, -0.0250, -0.0250,  0.0063],
          [ 0.0063, -0.0060, -0.0060, -0.0060,  0.0063],
          [ 0.0063,  0.0110,  0.0110,  0.0110,  0.0063],
          [ 0.0063,  0.0063,  0.0063,  0.0063,  0.0063],
          [ 0.0063,  0.0063,  0.0063,  0.0063,  0.0063]]],


        [[[-0.0063, -0.0063, -0.0063,  0.0250,  0.0250],
          [-0.0063, -0.0063, -0.0063,  0.0250,  0.0250],
          [-0.0063, -0.0063, -0.0063, -0.0063, -0.0063],
          [-0.0091, -0.0091, -0.0063, -0.0063, -0.0063],
          [-0.0091, -0.0091, -0.0063, -0.0063, -0.0063]],

         [[ 0.0063,  0.0063,  0.0063, -0.0250, -0.0250],
          [ 0.0063,  0.0063,  0.0063, -0.0250, -0.0250],
          [ 0.0063,  0.0063,  0.0063,  0.0063,  0.0063],
          [ 0.0091,  0.0091,  0.0063,  0.0063,  0.0063],
          [ 0.0091,  0.0091,  0.0063,  0.0063,  0.0063]]]], device='cuda:0')

Experiment6 : use FullCrossEntropyLoss with weight
Loss = -1.0764923095703125
inputs gradient = tensor([[[[-0.0500,  0.0500,  0.0500,  0.0500, -0.0500],
          [-0.0500,  0.0272,  0.0272,  0.0272, -0.0500],
          [-0.0500, -0.0272, -0.0272, -0.0272, -0.0500],
          [-0.0500, -0.0500, -0.0500, -0.0500, -0.0500],
          [-0.0500, -0.0500, -0.0500, -0.0500, -0.0500]],

         [[ 0.0500, -0.0500, -0.0500, -0.0500,  0.0500],
          [ 0.0500, -0.0272, -0.0272, -0.0272,  0.0500],
          [ 0.0500,  0.0272,  0.0272,  0.0272,  0.0500],
          [ 0.0500,  0.0500,  0.0500,  0.0500,  0.0500],
          [ 0.0500,  0.0500,  0.0500,  0.0500,  0.0500]]],


        [[[-0.0500, -0.0500, -0.0500,  0.0500,  0.0500],
          [-0.0500, -0.0500, -0.0500,  0.0500,  0.0500],
          [-0.0500, -0.0500, -0.0500, -0.0500, -0.0500],
          [-0.0361, -0.0361, -0.0500, -0.0500, -0.0500],
          [-0.0361, -0.0361, -0.0500, -0.0500, -0.0500]],

         [[ 0.0500,  0.0500,  0.0500, -0.0500, -0.0500],
          [ 0.0500,  0.0500,  0.0500, -0.0500, -0.0500],
          [ 0.0500,  0.0500,  0.0500,  0.0500,  0.0500],
          [ 0.0361,  0.0361,  0.0500,  0.0500,  0.0500],
          [ 0.0361,  0.0361,  0.0500,  0.0500,  0.0500]]]], device='cuda:0')
'''