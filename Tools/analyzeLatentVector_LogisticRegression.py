# Analyze the correlation between latent vector and its corresponding response

# dicesFilePath =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/predictResult/20191023_153046/patientDice.json"
# latentVectorDir =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/latent/latent_20191023_153046"
dicesFilePath =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/predictResult/20191025_102445/patientDice.json"
latentVectorDir =  "/home/hxie1/data/OvarianCancerCT/primaryROI1_1_3/latent/latent_20191025_102445"
patientResponsePath = "/home/hxie1/data/OvarianCancerCT/patientResponseDict.json"

# aList = range(0,85,2)  #dice range 0% to 85%, step 2%
aList = range(92,97,1)  #dice range 92% to 97%, step 1%
diceThresholdList=[x/100 for x in aList]
accuracyThreshold = 0.71  # for each feature
F,H,W = 1536,3,3  #Features, Height, Width of latent vector

import json
import numpy as np
import os
import matplotlib.pyplot as plt
import torch

def main():
    # patient response
    with open(patientResponsePath) as f:
        patientResponse = json.load(f)

    # filter Dice
    with open(dicesFilePath) as f:
        rawPatientDice = json.load(f)
    print(f"latent dir: {latentVectorDir}")
    print(f"There are total {len(rawPatientDice)} patients.")
    print(f"Each patient has a latent vector of size {(F,H,W)}")
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
        X = np.empty((F, H, W, N), dtype=np.float)  # latent vectors
        Y01 = np.empty((1, N), dtype=np.int)  # response in 0, 1 range
        for i, key in enumerate(list(patientDice)):
            Y01[0, i] = patientResponse[key]
            filePath = os.path.join(latentVectorDir, key + ".npy")
            V = np.load(filePath)
            assert (F, H, W) == V.shape
            X[:, :, :, i] = V
        response1Rate.append(Y01.sum() / N)

        # normalize latentV along patient dimension
        mean = np.mean(X, axis=3)
        std = np.std(X, axis=3)
        mean = np.reshape(np.repeat(mean, N, axis=2), X.shape)
        std = np.reshape(np.repeat(std, N, axis=2), X.shape)
        X = (X - mean) / std

        # Analysis: logistic loss =\sum (-y*log(sigmoid(x))-(1-y)*log(1-sigmoid(x)))
        # here W0 and W1 has a shape of (F,H, W)
        device = 3
        lr = 0.01
        nIteration = 100
        W0 = torch.zeros((F, H, W), dtype=torch.float, requires_grad=True, device=device)
        W1 = torch.zeros((F, H, W), dtype=torch.float, requires_grad=True, device=device)
        W1.data.fill_(0.01)
        for _ in range(0, nIteration):
            loss = torch.zeros((F, H, W), dtype=torch.float, device=device)
            if W0.grad is not None:
                W0.grad.data.zero_()
            if W1.grad is not None:
                W1.grad.data.zero_()
            for i in range(0,N):
                y = Y01[0,i]
                x = torch.from_numpy(X[:,:,:,i]).type(torch.float32).to(device)
                sigmoidx = torch.sigmoid(W0+W1*x)
                loss += -y*torch.log(sigmoidx)-(1-y)*torch.log(1-sigmoidx)
            loss = loss/N

            # backward
            loss.backward(gradient=torch.ones(loss.shape).to(device))
            # update W0 and W1
            W0.data -= lr*W0.grad.data  # we must use data, otherwise, it changes leaf property.
            W1.data -= lr*W1.grad.data

        W0 = W0.cpu().detach().numpy()
        W1 = W1.cpu().detach().numpy()

        W1Ex = np.reshape(np.repeat(W1, N, axis=2), X.shape)
        W0Ex = np.reshape(np.repeat(W0, N, axis=2), X.shape)

        sigmoidX = 1.0 / (1.0 + np.exp(-(W0Ex + W1Ex * X)))
        predictX = (sigmoidX >= 0.5).astype(np.int)
        Y = np.reshape(np.repeat(Y01, F * H * W, axis=0), X.shape)
        accuracyX = ((predictX - Y) == 0).sum(axis=3) / N

        minAccuracy.append(accuracyX.min())
        meanAccuracy.append(accuracyX.mean())
        medianAccuracy.append(np.median(accuracyX))
        maxAccuracy.append(accuracyX.max())

        accuracyBig = accuracyX >= accuracyThreshold
        numBestFeaturesTemp = accuracyBig.sum()
        numBestFeatures.append(numBestFeaturesTemp)

        print(f"fiinished dice {diceThreshold}...")

    # print table:
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
    f = plt.figure(1)
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

    f = plt.figure(2)
    plt.plot(diceThresholdList, rateBestFeatures)
    plt.gca().set_ylim([0, 1.0])
    plt.title(f"Rate of Best Features on different dice thresholds")
    plt.xlabel('Dice Thresholds')
    plt.ylabel('Rate of Best Features')
    plt.savefig(os.path.join(latentVectorDir, f"rateBestFeatures.png"))

if __name__ == "__main__":
    main()



