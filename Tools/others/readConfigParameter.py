
import torch

configDir = "/home/hxie1/data/OCT_Tongren/numpy/10FoldCVForMultiSurfaceNet/netParameters/SurfacesUnet/expTongren_9Surfaces_SoftConst_20200808_CV0_8Grad_LearnPair_Pretrain_LR1/realtime"
configFile = configDir + "/ConfigParameters.pt"

configDict = torch.load(configFile)

print(f"Information in {configFile}\n")
for key, value in configDict.items():
    print(f"\t{key}:{value}")

