# Test large matrix inverse

import torch
import time

N = 12*1024
device = torch.device("cuda:3")

startTime = time.time()
M = torch.rand((N,N), device=device,requires_grad=True)
identityM = torch.eye(N, device=device)*0.01
M = M+identityM
MInv = torch.inverse(M)
memorysummary = torch.cuda.max_memory_allocated(device=device)
runTime = time.time()-startTime
print(f"Matrix shape: {M.shape}")
print(f"===Matrix Inverse running time: {runTime} seconds.")  # about 3.9 seconds.
print(f"memory usage:  {memorysummary} byte\n")  #1.6GB
verify =  torch.mm(M, MInv)

print(f"verify[1000,1000] ={verify[1000,1000]} ")
print(f"verify[1000,100] ={verify[1000,100]} ")

'''
Matrix shape: torch.Size([10240, 10240])
===Matrix Inverse running time: 3.9061315059661865 seconds.
memory usage:  1680343040 byte

matrix memory: 10240*10240*4 = 419430400 byte = 419MB

==============
Matrix shape: torch.Size([12288, 12288])
===Matrix Inverse running time: 4.199603319168091 seconds.
memory usage:  2419064832 byte

verify[1000,1000] =0.9997560977935791 
verify[1000,100] =5.3988151194062084e-05 

'''