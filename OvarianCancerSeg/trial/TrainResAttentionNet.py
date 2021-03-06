# train ResNeXt-based Attention Net

import datetime
import torch.nn as nn
import torch.optim as optim
import logging

from ResponsePrediction.OCDataSet import *
from utilities.FilesUtilities import *
from utilities.MeasureUtilities import *
from OvarianCancerSeg.trial.ResAttentionNet import ResAttentionNet
from OvarianCancerSeg.OCDataTransform import *
from framework.NetMgr import NetMgr

logNotes = r'''
Major program changes: 
            ResNeXt-based Attention Net: use 2D network to implement 3D convolution without losing 3D context information. 
            0   the input is a 3D full volume without any cropping; 
            1   Use slices as features channels in convolutions,  and use 1*1 convolution along slices direction to implement z direction convolution followed by 3*3 convolutino inside slice planes;
                It just uses three cascading 2D convolutions (first z, then xy, and z direction again) to implement 3D convolution, like in the paper of ResNeXt below.
                The benefits of this design:
                A   reduce network parameters, hoping to reducing overfitting;
                B   speed up training;
                C   this implemented 3D convolutions are all in full slices space;
            2   use group convolution to implement thick slice convolution to increase the network representation capability;
            3   Use ResNeXt-based module like Paper "Aggregated Residual Transformations for Deep Neural Networks " 
                (Link: http://openaccess.thecvf.com/content_cvpr_2017/html/Xie_Aggregated_Residual_Transformations_CVPR_2017_paper.html);
            4   use rich 2D affine transforms slice by slice and concatenate them to implement 3D data augmentation;
            5   20% data for independent test, remaining 80% data for 4-fold cross validation;
            6   add lossweight to adjust positive samples to 3/7 posweight in BCEWithLogitsLoss;
            
            Update:
            1    reduced network parameters to 3.14 million in July 27th, 2019, 0840am
            2    at 15:00 of July 27th, 2019, reduce network parameter again. Now each stage has 160 filters, with 1.235 million parameters
            3    keep 2) parameter, change all maxpooling into average pooling.
            4    At July 29th 09:37am, 2019, reduce filters to 96 to further reduce parameters, keep avgPool.
            5    at July 29th 11:25am, 2019,  reduce filter number to 48, and redue one stage
            6    at July 29th 12:41, 2019:
                    add GPUID in command line;
                    use SGD optimizer, instead of Adam
                    add numbers of filters along deeper layer with step 12.
                    add saveDir's tims stamp;
            7    at July 29th 15:18, 2019,
                    change learning rate step_size = 5 from 10;
                    before FC, we use conv2d
                    learning rate start at 0.5.
            8    at July 30th 03:00, 2019:
                    add learning rate print;
                    use convStride =2;
                    add filter number by 2 times along deeper layers.
            9    at July 30th, 10:13, 2019:
                    add MaxPool2d in stage1;
                    add final filters to 2048.
            10   at July 30th, 15:23, 2019
                    final conv layer filter number: 1024
            11   at Aug 10th, 2019:
                    A. Add new patient data; and exclude non-standard patient data;
                    B. test the k-th fold,  validation on the (k+1)th fold;
                    C. new inputsize: 231*251*251 with pixels size 3*2*2 mm
                    D. window level shresthold [0,300]
                    E. put data padding in to converting from nrrd to numpy;
                    F. Add STN network as first laye of network
                    G. change input data into gaussian normalization in slice by slice; (x-mean)/std;
            12   Aug 12th, 2019
                    A. fix the bug that SITk reads int imape, and normalization into interger error;
                    B  test without SPN.           
            13   Aug 13th, 2019
                    A change input data into Gausssian distribution with non-zero mean,
                      it will make the padding zero do not occupy meaning of gaussian distribution.        
                    B add filters in the ResNeXt network to 128 at first stage, and reduce batchSize to 3. 
                    C Add STN at the beginning of the ResNeXt network
            14   Aug 14th, 2019
                    A. Fix the Bug the STN convert all image into 0 problem;
                    B. change DataTransform: change shear into [-30, 30], and add scale[0.6,1.2]
                    C  put STN at teh begginning of the network;
                    D  change optimizer from SGD to Adam; and change learning rate decay with gamma=0.5 per 20 steps.                                             
            15   Aug 16th, 2019
                    A The affine matrix in the STN is divided by its spectral norm;
                    B All conv layer add spectralNorm, while all FC layer do not add spectral Norm;
                    C reduce initial LR at 0.0001, and decay step to 30.
            16   Aug 17th, 2019
                    A  Cancel STN;
                    B  Add LeakyReLU;
                    C  before final FC layer, add ReLU and LocalResponseNorm   
            17   Aug 17th, 2019:10:44am
                    A enable STN;
                    B STN support LeakyReLU and localResponseNorm  
            18   Aug 17th, 2019 14:38 pm
                    A  del STN at beginining;
                    B  put STN at final 2 layer before FC. 
            19  Aug 17th 18:09 2019
                    A add surgical result file support;                    
            20  Aug 18th 08:00 am 2019
                    A  change all bias in Conv2d, and Linear into True.   
            21  Aug 19th 10:33am 2019
                    A initalize the bias in the final Linear layer as 0.3; (1-2*0.65 = -0.3)
                    16:17 pm:
                    B  add inductive bias 0.3 in the network forward function. 
                    C  initial LR =0.1, with decay steps =30                          
            22  Aug 20th 10:24am 2019
                    A change inductive bias = 0.2;
                    16:29pm:
                    B add modulation factor in the STN
            23  Aug 21th, 10:16, 2019
                    A delete the inductive bias in the final FC.  
                    15:47 pm
                    B change LRscheduler into MultiStepLR;
            24  Aug 22nd, 11:14, 2019
                    A replace ResNeXtBlock with DeformConvBlock in the stage3,4,5.
            25  Agu 23th 10:31, 2019
                    A in stage 3,4,4, reduce DeformConnBlock into 1 block;
                    B reduce the final FC layer width into 512.
                    15:10pm
                    C before regression with bias = 0, nomalize x. 
            26   Aug 24th, 2019, 13:42
                     A change + into - in all ResNeXtBlock, DeformConv2D, and STN;
                       Rational: deduct irrelevant features.                 
                    
                          
            
Discarded changes:                  
                  

Experiment setting:
Input CT data: maximum size 140*251*251 (zyx) of 3D numpy array with spacing size(5*2*2)
Ground truth: response binary label

Predictive Model: 

response Loss Function:  BCELogitLoss

Data:   total 220 patients, 5-fold cross validation, test 45, validation 45, and training 130.  

Training strategy: 

          '''


def printUsage(argv):
    print("============Train ResAttentionNet for Ovarian Cancer =============")
    print("Usage:")
    print(argv[0],
          "<netSavedPath> <scratch> <fullPathOfData>  <fullPathOfGroundTruthFile> k  GPUID_List")
    print("where: \n"
          "       scratch =0: continue to train basing on previous training parameters; scratch=1, training from scratch.\n"
          "       k=[0, K), the k-th fold in the K-fold cross validation.\n"
          "       GPUIDList: 0,1,2,3, the specific GPU ID List, separated by comma\n")

def printPartNetworkPara(epoch, net): # only support non-parallel
    print(f"Epoch: {epoch}   =================")
    print("FC.bias = ", net.m_fc1.bias.data)
    print("STN5 bias = ", net.m_stn5.m_regression.bias.data)
    print("STN4 bias = ", net.m_stn4.m_regression.bias.data)
    print("gradient at FC.bias=", net.m_fc1.bias._grad)
    print("\n")


def main():
    if len(sys.argv) != 7:
        print("Error: input parameters error.")
        printUsage(sys.argv)
        return -1

    netPath = sys.argv[1]
    scratch = int(sys.argv[2])
    dataInputsPath = sys.argv[3]
    groundTruthPath = sys.argv[4]
    k = int(sys.argv[5])
    GPUIDList = sys.argv[6].split(',')  # choices: 0,1,2,3 for lab server.
    GPUIDList = [int(x) for x in GPUIDList]
    inputSuffix = ".npy"

    curTime = datetime.datetime.now()
    timeStr = f"{curTime.year}{curTime.month:02d}{curTime.day:02d}_{curTime.hour:02d}{curTime.minute:02d}{curTime.second:02d}"

    if '/home/hxie1/' in netPath:
        trainLogFile = f'/home/hxie1/Projects/OvarianCancer/trainLog/log_ResAttention_CV{k:d}_{timeStr}.txt'
        isArgon = False
    elif '/Users/hxie1/' in netPath:
        trainLogFile = f'/Users/hxie1/Projects/OvarianCancer/trainLog/log_ResAttention_CV{k:d}_{timeStr}.txt'
        isArgon = True
    else:
        print("output net path should be full path.")
        return

    logging.basicConfig(filename=trainLogFile, filemode='a+', level=logging.INFO, format='%(message)s')

    if scratch>0:
        netPath = os.path.join(netPath, timeStr)
        print(f"=============training from sratch============")
        logging.info(f"=============training from sratch============")
    else:
        print(f"=============training inheritates previous training of {netPath} ============")
        logging.info(f"=============training inheritates previous training of {netPath} ============")

    print(f'Program ID of Predictive Network training:  {os.getpid()}\n')
    print(f'Program commands: {sys.argv}')
    print(f'Training log is in {trainLogFile}')
    print(f'.........')

    logging.info(f'Program ID: {os.getpid()}\n')
    logging.info(f'Program command: \n {sys.argv}')
    logging.info(logNotes)

    logging.info(f'\nProgram starting Time: {str(curTime)}')
    logging.info(f"Info: netPath = {netPath}\n")

    K_fold = 5
    logging.info(f"Info: this is the {k}th fold leave for test in the {K_fold}-fold cross-validation.\n")
    dataPartitions = OVDataPartition(dataInputsPath, groundTruthPath, inputSuffix, K_fold, k, logInfoFun=logging.info)

    testTransform = OCDataTransform(0)
    trainTransform = OCDataTransform(0.9)
    validationTransform = OCDataTransform(0)

    trainingData = OVDataSet('training', dataPartitions,  transform=trainTransform, logInfoFun=logging.info)
    validationData = OVDataSet('validation', dataPartitions,  transform=validationTransform, logInfoFun=logging.info)
    testData = OVDataSet('test', dataPartitions, transform=testTransform, logInfoFun=logging.info)

    # ===========debug==================
    oneSampleTraining = False  # for debug
    useDataParallel = True  if len(GPUIDList)>1 else False # for debug
    # ===========debug==================

    batchSize = 4*len(GPUIDList)
    # for Regulare Conv:  3 is for 1 GPU, 6 for 2 GPU
    # For Deformable Conv: 4 is for 1 GPU, 8 for 2 GPUs.

    numWorkers = 0
    logging.info(f"Info: batchSize = {batchSize}\n")

    net = ResAttentionNet()
    # Important:
    # If you need to move a model to GPU via .cuda(), please do so before constructing optimizers for it.
    # Parameters of a model after .cuda() will be different objects with those before the call.
    device = torch.device(f"cuda:{GPUIDList[0]}" if torch.cuda.is_available() else "cpu")
    net.to(device)

    optimizer = optim.Adam(net.parameters(), lr=0.1, weight_decay=0)
    #optimizer = optim.SGD(net.parameters(), lr=0.00001, momentum=0.9)
    net.setOptimizer(optimizer)

    # lrScheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)
    lrScheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=[50, 150, 300], gamma=0.1)

    # Load network
    netMgr = NetMgr(net, netPath, device)

    bestTestPerf = 0
    if 2 == len(getFilesList(netPath, ".pt")):
        netMgr.loadNet("train")  # True for train
        logging.info(f'Program loads net from {netPath}.')
        bestTestPerf = netMgr.loadBestTestPerf()
        logging.info(f'Current best test performance: {bestTestPerf}')
    else:
        logging.info(f"=== Network trains from scratch ====")

    logging.info(net.getParametersScale())

    # for imbalance training data for BCEWithLogitsLoss
    if "patientResponseDict" in  groundTruthPath:
        posWeightRate = 0.35/0.65
        logging.info("This predict optimal response.")
    elif "patientSurgicalResults" in groundTruthPath:
        posWeightRate = 0.23/0.77
        logging.info("This predict surgical results.")
    else:
        posWeightRate = 1.0
        logging.info("!!!!!!! Some thing wrong !!!!!")
        return

    bceWithLogitsLoss = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([posWeightRate]).to(device, dtype=torch.float), reduction="sum")
    net.appendLossFunc(bceWithLogitsLoss, 1)

    if useDataParallel:
        nGPU = torch.cuda.device_count()
        if nGPU > 1:
            logging.info(f'Info: program will use GPU {GPUIDList} from all {nGPU} GPUs.')
            net = nn.DataParallel(net, device_ids=GPUIDList, output_device=device)

    if useDataParallel:
        logging.info(net.module.lossFunctionsInfo())
    else:
        logging.info(net.lossFunctionsInfo())

    epochs = 1500000

    logging.info(f"\nHints: Optimal_Result = Yes = 1,  Optimal_Result = No = 0 \n")

    logging.info(f"Epoch" + f"\tLearningRate"\
                 + f"\t\tTrLoss" + f"\tAccura" + f"\tTPR_r" + f"\tTNR_r" \
                 + f"\t\tVaLoss" +  f"\tAccura" + f"\tTPR_r" + f"\tTNR_r" \
                 + f"\t\tTeLoss" +  f"\tAccura" + f"\tTPR_r" + f"\tTNR_r" )  # logging.info output head

    oldTestLoss = 1000

    for epoch in range(0, epochs):
        random.seed()
        if useDataParallel:
            lossFunc = net.module.getOnlyLossFunc()
        else:
            lossFunc = net.getOnlyLossFunc()
        # ================Training===============
        net.train()
        trainingLoss = 0.0
        trainingBatches = 0

        epochPredict = None
        epochResponse = None
        responseTrainAccuracy = 0.0
        responseTrainTPR = 0.0
        responseTrainTNR = 0.0


        for inputs, responseCpu in data.DataLoader(trainingData, batch_size=batchSize, shuffle=True, num_workers=numWorkers):
            inputs = inputs.to(device, dtype=torch.float)
            gt = responseCpu.to(device, dtype=torch.float)

            optimizer.zero_grad()
            xr = net.forward(inputs)
            loss = lossFunc(xr, gt)

            loss.backward()
            optimizer.step()
            batchLoss = loss.item()

            # accumulate response and predict value
            if epoch % 5 == 0:
                batchPredict = (xr>= 0).detach().cpu().numpy().flatten()
                epochPredict = np.concatenate(
                    (epochPredict, batchPredict)) if epochPredict is not None else batchPredict
                batchGt = responseCpu.detach().numpy()
                epochResponse = np.concatenate(
                    (epochResponse, batchGt)) if epochResponse is not None else batchGt


            trainingLoss += batchLoss
            trainingBatches += 1

            if oneSampleTraining:
                break

        if 0 != trainingBatches:
            trainingLoss /= trainingBatches
            lrScheduler.step()

        if epoch % 5 == 0:
            responseTrainAccuracy = getAccuracy(epochPredict, epochResponse)
            responseTrainTPR = getTPR(epochPredict, epochResponse)[0]
            responseTrainTNR = getTNR(epochPredict, epochResponse)[0]

        else:
            continue  # only epoch %5 ==0, run validation set.

        # printPartNetworkPara(epoch, net)
        # ================Validation===============
        net.eval()

        validationLoss = 0.0
        validationBatches = 0

        epochPredict = None
        epochResponse = None
        responseValidationAccuracy = 0.0
        responseValidationTPR = 0.0
        responseValidationTNR = 0.0

        with torch.no_grad():
            for inputs, responseCpu in data.DataLoader(validationData, batch_size=batchSize, shuffle=False, num_workers=numWorkers):
                inputs = inputs.to(device, dtype=torch.float)
                gt     = responseCpu.to(device, dtype=torch.float)  # return a copy

                xr = net.forward(inputs)
                loss = lossFunc(xr, gt)
                batchLoss = loss.item()

                # accumulate response and predict value

                batchPredict = (xr>= 0).detach().cpu().numpy().flatten()
                epochPredict = np.concatenate(
                    (epochPredict, batchPredict)) if epochPredict is not None else batchPredict
                batchGt = responseCpu.detach().numpy()
                epochResponse = np.concatenate(
                    (epochResponse, batchGt)) if epochResponse is not None else batchGt

                validationLoss += batchLoss
                validationBatches += 1

                if oneSampleTraining:
                    break


            if 0 != validationBatches:
                validationLoss /= validationBatches

            if epoch % 5 == 0:
                responseValidationAccuracy = getAccuracy(epochPredict, epochResponse)
                responseValidationTPR = getTPR(epochPredict, epochResponse)[0]
                responseValidationTNR = getTNR(epochPredict, epochResponse)[0]

            # ================Independent Test===============
            net.eval()

            testLoss = 0.0
            testBatches = 0

            epochPredict = None
            epochResponse = None
            responseTestAccuracy = 0.0
            responseTestTPR = 0.0
            responseTestTNR = 0.0

            with torch.no_grad():
                for inputs, responseCpu in data.DataLoader(testData, batch_size=batchSize, shuffle=False, num_workers=numWorkers):
                    inputs = inputs.to(device, dtype=torch.float)
                    gt = responseCpu.to(device, dtype=torch.float)  # return a copy

                    xr = net.forward(inputs)
                    loss = lossFunc(xr, gt)

                    batchLoss = loss.item()

                    # accumulate response and predict value

                    batchPredict = (xr>= 0).detach().cpu().numpy().flatten()
                    epochPredict = np.concatenate(
                        (epochPredict, batchPredict)) if epochPredict is not None else batchPredict
                    batchGt = responseCpu.detach().numpy()
                    epochResponse = np.concatenate(
                        (epochResponse, batchGt)) if epochResponse is not None else batchGt

                    testLoss += batchLoss
                    testBatches += 1

                    if oneSampleTraining:
                        break

                if 0 != testBatches:
                    testLoss /= testBatches

                if epoch % 5 == 0:
                    responseTestAccuracy = getAccuracy(epochPredict, epochResponse)
                    responseTestTPR = getTPR(epochPredict, epochResponse)[0]
                    responseTestTNR = getTNR(epochPredict, epochResponse)[0]


        # ===========print train and test progress===============
        learningRate  = lrScheduler.get_lr()[0]
        outputString  = f'{epoch}' +f'\t{learningRate:1.4e}'
        outputString += f'\t\t{trainingLoss:.4f}'       + f'\t{responseTrainAccuracy:.4f}'      + f'\t{responseTrainTPR:.4f}'      + f'\t{responseTrainTNR:.4f}'
        outputString += f'\t\t{validationLoss:.4f}'   + f'\t{responseValidationAccuracy:.4f}' + f'\t{responseValidationTPR:.4f}' + f'\t{responseValidationTNR:.4f}'
        outputString += f'\t\t{testLoss:.4f}'         + f'\t{responseTestAccuracy:.4f}'       + f'\t{responseTestTPR:.4f}'       + f'\t{responseTestTNR:.4f}'
        logging.info(outputString)

        # =============save net parameters==============
        if trainingLoss < float('inf') and not math.isnan(trainingLoss) :
            netMgr.saveNet()
            if responseValidationAccuracy > bestTestPerf or (responseValidationAccuracy == bestTestPerf and validationLoss < oldTestLoss):
                oldTestLoss = validationLoss
                bestTestPerf = responseValidationAccuracy
                netMgr.saveBest(bestTestPerf)
            if trainingLoss <= 0.02: # CrossEntropy use natural logarithm . -ln(0.98) = 0.0202. it means training accuracy  for each sample gets 98% above
                logging.info(f"\n\n training loss less than 0.02, Program exit.")
                break
        else:
            logging.info(f"\n\nError: training loss is infinity. Program exit.")
            break

    torch.cuda.empty_cache()
    logging.info(f"\n\n=============END of Training of ResAttentionNet Predict Model =================")
    print(f'Program ID {os.getpid()}  exits.\n')
    curTime = datetime.datetime.now()
    logging.info(f'\nProgram Ending Time: {str(curTime)}')


if __name__ == "__main__":
    main()
