# measure max Rift

import numpy as np

# all label files
labelFiles=["/home/hxie1/data/OCT_Tongren/numpy/10FoldCVForMultiSurfaceNet/training/surfaces_CV0.npy",\
            "/home/hxie1/data/OCT_Tongren/numpy/10FoldCVForMultiSurfaceNet/validation/surfaces_CV0.npy",\
            "/home/hxie1/data/OCT_Tongren/numpy/10FoldCVForMultiSurfaceNet/test/surfaces_CV0.npy"]

for i, labelFile in enumerate(labelFiles):
    surfaces = np.load(labelFile)  # BxNxW
    S = np.concatenate((S,surfaces), axis=0) if 0 !=i else surfaces
    R = surfaces[:,1:,:] - surfaces[:,0:-1,:]  # size: Bx(N-1)xW
    Rs = np.concatenate((Rs,R), axis=0) if 0 !=i else R

print(f"S.shape= {S.shape}")
print(f"Rs.shape= {Rs.shape}")

maxS = np.amax(S)
minS = np.amin(S)

maxRift    = np.amax(Rs)
meanRift   = np.mean(Rs)
minRift    = np.amin(Rs)
medianRift = np.median(Rs)



print(f"minS = {minS}, maxS = {maxS}")
print(f"maxRift= {maxRift}, meanRift={meanRift}, minRift={minRift}, medianRift={medianRift}")

''' Tongren measurement result
S.shape= (1457, 9, 512)
Rs.shape= (1457, 8, 512)
minS = 89, maxS = 406
maxRift= 49, meanRift=9.296583271222975, minRift=0, medianRift=7.0

'''
