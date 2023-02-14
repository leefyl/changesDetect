# %% [markdown]
# ## Run the actual function
# the script is organised in 2 steps. `getSignal` and `returnFrameOfInterestIndexes`
# 
# in the first the algorithm look at the number of pixel changing between frame 'i' and the n adjacent frames (`nFrameForBaseline`). In the second step the algorithm analyse the obtained signal and determine if that signal can be related to a bird or not..
# 
# the second step is simple threshold (`threshold`) between frame 'i' and the frame 'i'+`timePdiff`
# the second step could be improved by using other approaches.
# 

# %%
def getSignal(folder, doSmooth = True, nFrameForBaseline = 13, noiseThreshold = 50, RGBframeToUse = 2):
    """
    This function does the following: 
        for each frame 'i' it averages the 'nFrameForBaseline' around 'i' ('i' included)
        look at the difference in pixel value between the baseline and the frame 'i'
        count how many pixel differ by a value higher than 'noiseThreshold'
        save the count and move on to the next frame.

    folder:     path to folder containing the pictures
    doSmooth:   boolean indicating if the picture should be smooth using the function 'ImageFilter.SMOOTH' from PIL library
    nFrameForBaseline:  numerical value indicating the number of frame to be used for the baseline
    noiseThreshold:     numerical value indicating the threshold where the signal is classified as noise. see below for extra information
    RGBframeToUse:      numerical value indicating which picture layer to use 1: 'red', 2: 'green', 3: 'blue'. if you want 
                        to use all of them you can modify the function in the script

    if the folder contains less or the same number of frames than the argument 'nFrameForBaseline', the function returns 0 and warns the user
    on the argument 'noiseThreshold':   
        if the current image does not differ for any pixel by more than the threshold value then a 0 will be written for that frame
    
    return a numerical list
    """
    from PIL import Image
    from PIL import ImageFilter
    import numpy as np

    # get a list of all frame names in the right order!
    listFrame = os.listdir(folder)
    listFrame = ["frame" + str(i) + ".jpg" for i in range(len(listFrame))]

    if len(listFrame) <= nFrameForBaseline:
        warnings.warn("folder: --" + folder + "-- was ignored as the number of frame is smaller or equal to the number of frame required for the baseline")
        return 0
    else:
        
        # return a dictionary with the first frame to consider for each frame. 
        #  needed as for frame 1 we cannot start at frame-6, but at frame0
        dicIndex = getBaselineIndexStart(len(listFrame), nFrameForBaseline) 

        res = []

        for currPicIndex in range(len(listFrame)):

            if currPicIndex == 0:

                baselineIndexStart = dicIndex.get(currPicIndex)
                # load images
                picBaseline = [[] for i in range(nFrameForBaseline)]
                for i in range(nFrameForBaseline):
                    picBaseline[i] = Image.open(folder + listFrame[baselineIndexStart + i])
                
                picTest = Image.open(folder + listFrame[currPicIndex])

                if doSmooth:
                    #   smooth
                    picTest = picTest.filter(ImageFilter.SMOOTH)
                    picBaseline = [i.filter(ImageFilter.SMOOTH) for i in picBaseline]

                # compute baseline
                arrBaseline = np.array([np.array(i) for i in picBaseline])
                baseLine = np.mean(arrBaseline, axis = 0)

            else:
                prevBaselineIndexStart = baselineIndexStart
                baselineIndexStart = dicIndex.get(currPicIndex)
                #   test if the previous and new baselin index start are identical.. will happen at the beginning and the end...if it's the case then no need to load new images.
                if prevBaselineIndexStart == baselineIndexStart:
                    picTest = Image.open(folder + listFrame[currPicIndex])
                    if doSmooth:
                        picTest = picTest.filter(ImageFilter.SMOOTH)
                else:
                    # remove first image in the set of images for the baseline and add the next one
                    picBaseline = picBaseline[1:]
                    picBaseline.append(Image.open(folder + listFrame[baselineIndexStart + nFrameForBaseline - 1]))
                    
                    picTest = Image.open(folder + listFrame[currPicIndex])
                    
                    if doSmooth:
                        #   smooth
                        picTest = picTest.filter(ImageFilter.SMOOTH)
                        picBaseline[-1] = picBaseline[-1].filter(ImageFilter.SMOOTH)

                    # compute baseline
                    arrBaseline = np.array([np.array(i) for i in picBaseline])
                    baseLine = np.mean(arrBaseline, axis = 0)

            #   process images
            picTest = np.array(picTest)

            #   compare image to baseline
            """     if you want to use all 3 layers 'R', 'G' and 'B' then just uncomment the line below and comment the next one which define 'imgDifference'    """
#           imgDifference = np.subtract(picTest, baseLine)
            imgDifference = np.subtract(picTest[:,:,RGBframeToUse], baseLine[:,:,RGBframeToUse])

            if (np.amin(imgDifference) < -noiseThreshold or np.amax(imgDifference) > noiseThreshold):
                #   compare  image to baseline
                imgDifferenceBool = (imgDifference > noiseThreshold) | (imgDifference < -noiseThreshold)
                res.append(imgDifferenceBool.sum())
            else:
                res.append(0)   # if no diff between current frame and baseline then 0
        return res



def returnFrameOfInterestIndexes(data, timePdiff = 6, threshold = 400):
    """
    function to return the index of frame of interest
    the current approach is to look at the difference in signal between the frame 'i' and the frame 
    'i' + 'timePdiff'. if the signal is higher than the 'threshold' it is then considered as being
    of interest

    data:       a numerical list resulting from function 'getSignal'
    timePdiff:  a numerical value
    threshold:  a numerical value

    return a dictionary
    """
    # compute difference
    res = []
    for i in range(len(data) - timePdiff):
        res.append(data[i] - data[i + timePdiff])

    for i in range(len(data) - timePdiff, len(data)):
        res.append(data[i] - data[i - timePdiff])

    # check for which time point difference is bigger than threshold
    biggerThan = [i for i in range(len(res)) if res[i] > threshold]
    return biggerThan




def getBaselineIndexStart(nFrame, nFrameBaseline):
    """
    the frame for the baseline are taken on both side of the frame being treated. however at the start 
    and the end this is not possible. therefore this function is here to return which frame is to be 
    used for the start of the baseline
    
    return where the baseline should start for each index
    """
    import math
    nFrameOnEachSide = math.floor(nFrameBaseline / 2)

    if nFrameBaseline % 2 == 0:
        OE = 0
    else:
        OE = 1

    resd = {}
    for currPicIndex in range(nFrame):
        if currPicIndex - nFrameOnEachSide >= 0 and currPicIndex + (nFrameOnEachSide + OE) <= nFrame:
            baselineIndexStart = currPicIndex - nFrameOnEachSide
        elif currPicIndex - nFrameOnEachSide < 0:
            baselineIndexStart = 0
        elif currPicIndex + nFrameOnEachSide > nFrame:
            baselineIndexStart = nFrame - (nFrameOnEachSide * 2 + OE)
        resd[currPicIndex] = baselineIndexStart
    return (resd)


