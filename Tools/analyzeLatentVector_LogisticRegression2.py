# Analyze the correlation between latent vector and its corresponding response

# this file is analyzing 1D latent vector(1536*1 per patient)

# dicesFilePath =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/predictResult/20191023_153046/patientDice.json"
# latentVectorDir =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/latent/latent_20191023_153046"
dicesFilePath =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/training/predict_20191207_135106/patientDice.json"
latentVectorDir =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/training/latent/latent_20191207_135106"
patientResponsePath = "/home/hxie1/data/OvarianCancerCT/patientResponseDict.json"

# aList = range(0,85,2)  #dice range 0% to 85%, step 2%
aList = range(80,95,1)  #dice range 82% to 95%, step 1%
diceThresholdList=[x/100 for x in aList]
accuracyThreshold = 0.8  # for each feature
F,W = 1536,1  #Features, Width of latent vector, per patient
gpuDevice = 3   #GPU ID
K = 10 # the top K maximum accuracy positions, it requres an even number.

import json
import numpy as np
import os
import matplotlib.pyplot as plt
import torch

def main():

    if K%2 != 0:
        print(f"program demands K is an even number")
        return

    # patient response
    with open(patientResponsePath) as f:
        patientResponse = json.load(f)

    # filter Dice
    with open(dicesFilePath) as f:
        rawPatientDice = json.load(f)
    print(f"latent dir: {latentVectorDir}")
    print(f"There are total {len(rawPatientDice)} patients.")
    print(f"Each patient has a latent vector of size {(F,W)}")
    print(f"Each feature alone predicts its response through a Logistic regression along patients dimension.")
    print(f"accuracy Threshold = {accuracyThreshold}, for each feature")

    validationSamples = []
    response1Rate= []
    averageDiceSamples = []
    minAccuracy  = []
    meanAccuracy = []
    medianAccuracy = []
    maxAccuracy  = []
    numBestFeatures = []  # num of features whose predicted accuracy is greater than specific threshold

    # For F*1 latent Vector

    for diceThreshold in diceThresholdList:
        patientDice = rawPatientDice.copy()
        for key in list(patientDice):
            if patientDice[key] < diceThreshold:
                del patientDice[key]
        N = len(patientDice)
        validationSamples.append(N)

        dices = 0.0
        for dice in patientDice.values():
            dices += dice
        averageDiceSamples.append(dices/N)

        # get response vector and assemble latent Vectors
        X = np.empty((F, N), dtype=np.float)  # latent vectors
        Y01 = np.empty((1, N), dtype=np.int)  # response in 0, 1 range
        for i, key in enumerate(list(patientDice)):
            Y01[0, i] = patientResponse[key]
            filePath = os.path.join(latentVectorDir, key + ".npy")
            print(f"{i} = {filePath}")
            V = np.load(filePath)
            print(f"V[0] = {V[0]}, V[1] = {V[1]}, V[2] = {V[2]}, ")
            assert (F,) == V.shape
            X[:,i] = V
        response1Rate.append(Y01.sum() / N)
        rawX = X.copy()

        # normalize latentV along patient dimension
        mean = np.mean(X, axis=1, keepdims=True)
        std = np.std(X, axis=1,keepdims=True)
        mean = np.repeat(mean, N, axis=1)
        std = np.repeat(std, N, axis=1)
        X = (X - mean) / std

        # Logistic Regression Analysis: logistic loss =\sum (-y*log(sigmoid(x))-(1-y)*log(1-sigmoid(x)))
        # here W0 and W1 each have a shape of (F,1)
        # sigmoid(x) = sigmoid(W0+W1*x)
        lr = 0.01
        nIteration = 200
        W0 = torch.zeros((F, 1), dtype=torch.float, requires_grad=True, device=gpuDevice)
        W1 = torch.zeros((F, 1), dtype=torch.float, requires_grad=True, device=gpuDevice)
        W1.data.fill_(0.01)
        for _ in range(0, nIteration):
            loss = torch.zeros((F, 1), dtype=torch.float, device=gpuDevice)
            if W0.grad is not None:
                W0.grad.data.zero_()
            if W1.grad is not None:
                W1.grad.data.zero_()
            for i in range(0,N):
                y = Y01[0,i]
                x = torch.from_numpy(X[:,i]).type(torch.float32).to(gpuDevice)
                sigmoidx = torch.sigmoid(W0+W1*x)
                loss += -y*torch.log(sigmoidx)-(1-y)*torch.log(1-sigmoidx)
            loss = loss/N

            # backward
            loss.backward(gradient=torch.ones(loss.shape).to(gpuDevice))
            # update W0 and W1
            W0.data -= lr*W0.grad.data  # we must use data, otherwise, it changes leaf property.
            W1.data -= lr*W1.grad.data

        W0 = W0.detach().cpu().numpy()
        W1 = W1.detach().cpu().numpy()

        W0Ex = np.repeat(W0, N, axis=1)
        W1Ex = np.repeat(W1, N, axis=1)

        sigmoidX = 1.0 / (1.0 + np.exp(-(W0Ex + W1Ex * X)))
        predictX = (sigmoidX >= 0.5).astype(np.int)
        Y = np.repeat(Y01, F, axis=0)
        accuracyX = ((predictX - Y) == 0).sum(axis=1) / N

        minAccuracy.append(accuracyX.min())
        meanAccuracy.append(accuracyX.mean())
        medianAccuracy.append(np.median(accuracyX))
        maxAccuracy.append(accuracyX.max())

        accuracyBig = accuracyX >= accuracyThreshold
        numBestFeaturesTemp = accuracyBig.sum()
        numBestFeatures.append(numBestFeaturesTemp)

        #  Analyze the locations of top accuracies.
        print(f"\nfinished dice {diceThreshold}...")
        k=K if numBestFeaturesTemp >= K else numBestFeaturesTemp
        print(f"Its top {k} accuracies location:")
        accuracyXFlat = np.squeeze(accuracyX)
        topKIndices = np.argpartition(accuracyXFlat, kth=-k)[-k:]
        print(f"indices:    {topKIndices}")
        print(f"accuracies: {accuracyXFlat[topKIndices]}")

        #draw logistic regression curves
        for i in range(0,k):
            f = topKIndices[i] # feature index
            #drawM: draw Matrix row 0 to 2: x, sigmoid(w0+w1*), y
            drawM = np.zeros((3, N), dtype=np.float)
            drawM[0,] = X[f,]
            drawM[1,] = 1.0 / (1.0 + np.exp(-(W0[f] + W1[f] * X[f,])))
            drawM[2,] = Y01
            drawM = drawM[:, drawM[0,:].argsort()]

            subplot = plt.subplot(k//2, 2, i+1)

            subplot.plot(drawM[0,], drawM[2,], 'gx')
            subplot.plot(drawM[0,], drawM[1,], 'r-')
            subplot.gca().set_ylim([0, 1.0])

            subplot.xlabel('normalized latent value')
            subplot.ylabel('Response')
            subplot.legend(f"feature_{f}")

        plt.title(f"Top {k} accuracy logistic regression")
        plt.show()
        plt.savefig(os.path.join(latentVectorDir, f"logisticRegress_diceThreshold{int(diceThreshold * 100)}.png"))

    # print table:
    print("\n")
    print(f"dice threshold list:    {diceThresholdList}")
    print(f"validation patients:    {validationSamples}")
    print(f"avgDice of validaiton:  {averageDiceSamples}")
    print(f"Rate of Response 1:     {response1Rate}")
    print(f"minAccuracy:            {minAccuracy}")
    print(f"meanAccuracy:           {meanAccuracy}")
    print(f"medianAccuracy:         {medianAccuracy}")
    print(f"maxAccuracy:            {maxAccuracy}")
    print(f"num of Best Features:   {numBestFeatures}")
    nFeatures = F*H*W
    rateBestFeatures = [x/(nFeatures) for x in numBestFeatures ]
    print(f"rate of Best Features:  {rateBestFeatures}")


    #draw table:
    fig = plt.figure(2)
    plt.plot(diceThresholdList, minAccuracy)
    plt.plot(diceThresholdList, meanAccuracy)
    plt.plot(diceThresholdList, medianAccuracy)
    plt.plot(diceThresholdList, maxAccuracy)
    plt.plot(diceThresholdList, response1Rate)
    plt.plot(diceThresholdList, averageDiceSamples)
    plt.gca().set_ylim([0, 1.0])
    plt.legend(('Min', 'Mean', 'median', 'Max', 'resp1Rate', 'avgDice'), loc='lower right')
    plt.title(f"Single-Feature prediciton on different dice thresholds")
    plt.xlabel('Dice Thresholds')
    plt.ylabel('Prediction Accuracy')
    plt.savefig(os.path.join(latentVectorDir, f"SingleFeaturePrediction.png"))

    fig = plt.figure(3)
    plt.plot(diceThresholdList, rateBestFeatures)
    plt.gca().set_ylim([0, 1.0])
    plt.title(f"Rate of Best Features on different dice thresholds")
    plt.xlabel('Dice Thresholds')
    plt.ylabel('Rate of Best Features')
    plt.savefig(os.path.join(latentVectorDir, f"rateBestFeatures.png"))

if __name__ == "__main__":
    main()


