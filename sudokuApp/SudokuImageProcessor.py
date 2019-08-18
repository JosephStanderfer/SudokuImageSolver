# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 15:46:27 2019

@author: josep
"""

import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
from scipy import ndimage
import math
from keras.models import load_model
from keras import backend as K
import tensorflow as tf


class sudokuImageProcessor():
    def __init__(self, image):
        self.imageOrig = None
        self.gridImage = None #used to hold resized image
        self.digitsDict = None
        self.probabilitiesDict = {}
        self.predictedGrid = np.zeros((9,9)) 

        #needed to prevent conflicts between tensorflow and the multiple flask threads
        self.session = tf.Session()
        self.graph = tf.get_default_graph()

        #load the image to be decoded during initialization
        #check that input is np.ndarray
        if not image.any() or type(image) is not np.ndarray:
            raise Exception('invalid image type pass in')
        # if image has multiple channels convert to grayscale in 2D array
        elif len(image.shape) == 2:
            self.imageOrig = self.resizeImage(image)   #rescale image to an appropriate size before saving it
        elif len(image.shape) == 3:   
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            self.imageOrig = self.resizeImage(image)   #rescale image to an appropriate size before saving it
        else:
            raise Exception('invalid image array shape:', image.shape)
        
        
        #finds sudoku grid within image and rotates/stretches image to fit grid
        self.gridImage, gridMask = self.stretchToGrid(self.imageOrig)
        
        #plt.subplot(121),plt.imshow(self.imageOrig, cmap='magma'),plt.title('Input')
        #plt.subplot(122),plt.imshow(self.gridImage, cmap='magma'),plt.title('Output')
        #plt.show()
        
        # process grid image by dividing it into 81 cells, identifying digit blobs, and using a 
        # Convnet model to predict the digit value
        self.digitsDict = self.extractDigitImages(self.gridImage, gridMask)
        self.predictedGrid, self.probabilitiesDict = self.predictDigitValues(self.digitsDict)
        
        
        
    def stretchToGrid(self, image):
        imageOrig = image.copy()
        imageMask = image.copy()
        
        imageMask = self.edgeConvolve(imageMask)
        
        #use adaptive threshold to clean up image
        imageMask = cv2.adaptiveThreshold(imageMask,255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,11,2)
        gridMask = self.createGridMask(imageMask)
        
        #crops the images to the outline of the sudoku grid
        gridImage, gridMask = self.straightenAndStretchImage(gridMask, imageOrig)
        
        return (gridImage, gridMask)
        
    def resizeImage(self, image):
        height, width = image.shape[:2]
        max_height = 500
        max_width = 500
        
        # only shrink if img is bigger than required
        if max_height < height or max_width < width:
            # get scaling factor
            scaling_factor = max_height / float(height)
            if max_width/float(width) < scaling_factor:
                scaling_factor = max_width / float(width)
            # resize image
            image = cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
        
        return image
        
    def edgeConvolve(self, image):
        #image edge detection convolution
        #uses blur kernel to soften image
        #uses lines kernel to highlight vertical and horizontal lines
        blurKernel = np.array([[1/9,1/9,1/9],[1/9,1/9,1/9],[1/9,1/9,1/9]])
        edgeKernel = np.array([[-1,-1,-1],[-1,5,-1],[-1,-1,-1]])
        kernelLoss = edgeKernel.shape[0]-1  # the number of pixels removed from the image width and height using this kernel
        height, width = image.shape
        
        
        #1 invert image
        image = (image * -1) + 255
        
        #create storage arrays
        outputImg = np.zeros(image.shape)
        paddedImg = np.zeros((height+kernelLoss, width+kernelLoss))
        paddedImg[1:-1, 1:-1] = image
        
        # fill padded edges with repeat of rows and columns, instead of 0's. avoid's creating line at edge
        paddedImg[0,1:-1] = image[0,0:] 
        paddedImg[paddedImg.shape[0]-1,1:-1] = image[image.shape[0]-1,0:]
        paddedImg[1:-1,0] = image[:,0]
        paddedImg[1:-1,paddedImg.shape[1]-1] = image[0:,image.shape[1]-1]
        
        #2 blur image
        for r in range(height):
            for c in range(width):
                kernelProduct = paddedImg[r:r+blurKernel.shape[0], c:c+blurKernel.shape[1]] * blurKernel
                outputImg[r,c] = kernelProduct.sum()
        
        
        #3 edge convolve
        paddedImg = np.zeros((height+kernelLoss, width+kernelLoss))
        paddedImg[1:-1, 1:-1] = outputImg
        # fill padded edges with repeat of rows and columns, instead of 0's. avoid's creating line at edge
        paddedImg[0,1:-1] = outputImg[0,0:] 
        paddedImg[paddedImg.shape[0]-1,1:-1] = outputImg[outputImg.shape[0]-1,0:]
        paddedImg[1:-1,0] = outputImg[:,0]
        paddedImg[1:-1,paddedImg.shape[1]-1] = outputImg[0:,outputImg.shape[1]-1]
        
        for r in range(height):
            for c in range(width):
                kernelProduct = paddedImg[r:r+edgeKernel.shape[0], c:c+edgeKernel.shape[1]] * edgeKernel
                outputImg[r,c] = kernelProduct.sum()#max(0, kernelProduct.sum()) #use ReLu formula on kernel sum
        
        #adjust pixels values to between 0 and 255
        outputImg += abs(outputImg.min())
        normalized = ((outputImg / outputImg.max()) *255)
        
        return normalized.astype(np.uint8)
        
    def createGridMask(self, image):
        # iterate through all the pixels in the image. floodfill all white pixels and retrieve the image mask
        # the mask with the largest bounding area will be the sudoku grid. return that mask to so that the corner
        # points of the grid can be found
        # help from https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
        
        height, width = image.shape
        # 8 is used if blobs have corners
        floodflags = 8
        floodflags |= cv2.FLOODFILL_MASK_ONLY
        floodflags |= (255 << 8)
        
        largestMask = None
        largestBoundingArea = 1
        
        #iterate through every 4th pixel in the image. floodfill white pixels and retrieve the image mask
        # the mask with the largest bounding area will be the sudoku grid
        for w in range(0,width,2): 
            for h in range(0,height,2):
                if image[h,w] > 200:    #only floodfill pixels that are white (such as the inverted lines of the grid)
                    mask = np.zeros((height+2,width+2),np.uint8)
                    seed = (w, h)  # starting point of floodfill
                    num,im,mask,rect = cv2.floodFill(image, mask, seed, (255,0,0), (10,)*3, (10,)*3, floodflags)
                    boundingArea = rect[2]*rect[3] #area of the bounding box of the floodfill mask
                    fillVsBoundingArea = num/boundingArea 
                    
                    #find largest shape in filter results by expected grid mask attributes
                    #typical fill area over bounding area is 0.118, 0.127
                    if boundingArea > largestBoundingArea and .05 < fillVsBoundingArea < .3:
                        largestMask = mask
                        largestBoundingArea = boundingArea
                        
        #if sudoku grid is not found throw error
        gridSizeVsImageSize = largestBoundingArea / (height* width)  #grid area should be at least 40% of the image
        if largestMask is None or gridSizeVsImageSize < 0.4:
            raise Exception('Grid not found in image')
        
        #blur grid mask to eliminate noise from flood fill
        gridMask = cv2.GaussianBlur(largestMask, (5, 5), 0)  
        
        return gridMask
    
    
    
    def createDigitMask(self, image, gridMask):
        # iterate through all the pixels in the image. floodfill all white pixels and retrieve the image mask
        # the mask with the largest bounding area will be the sudoku grid. return that mask to so that the corner
        # points of the grid can be found
        # help from https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
        
        height, width = image.shape
        # 8 is used if blobs have corners
        floodflags = 8
        floodflags |= cv2.FLOODFILL_MASK_ONLY
        floodflags |= (255 << 8)
        
        largestMask = None
        largestCenter = (0,0)
        largestFill = 0
        largestRect = None
        
        #iterate through every 4th pixel in the image. floodfill white pixels and retrieve the image mask
        # the mask with the largest bounding area will be the sudoku grid
        for w in range(0,width,2): 
            for h in range(0,height,2):
                if image[h,w] > 200 and gridMask[h, w] == 0:    #only floodfill pixels that are white and not part of the grid mask
                    mask = np.zeros((height+2,width+2),np.uint8)
                    seed = (w, h)  # starting point of floodfill
                    num,im,mask,rect = cv2.floodFill(image, mask, seed, (255,0,0), (10,)*3, (10,)*3, floodflags)
                    boundingArea = rect[2]*rect[3] #area of the bounding box of the floodfill mask
                    fillVsBoundingArea = num/boundingArea 
                    center = (rect[1] + 0.5*rect[3], rect[0] + 0.5*rect[2]) 
                    #find largest shape in filter results by expected digit mask attributes
                    if num > largestFill and (0.05*width*height) < boundingArea < (0.5 *width*height) \
                                        and 0.1 < fillVsBoundingArea < 0.9 \
                                        and 0.2*height < center[0] < 0.8*height\
                                        and 0.2*width < center[1] < 0.8*width:
                        largestMask = mask
                        largestCenter = center
                        largestFill = num
                        largestRect = rect
                        
        #if digit is not found return empty mask
        if largestMask is None:
            return None
        else:
            #center the digit within the mask
            largestMask = np.roll(largestMask, int((height//2) - (largestCenter[0])) , axis = 0)
            largestMask = np.roll(largestMask, int((width//2) - (largestCenter[1])) , axis = 1)
            
            #zero out small values and blur grid mask to eliminate noise from flood fill
            largestMask[largestMask < 10] = 0
            digitMask = cv2.GaussianBlur(largestMask, (5, 5), 0)
            
            #cut digitMask to make digit relatively bigger
            crop = (int) (height - (largestRect[3] / 0.8))//2  #the height of the image minus the new image height (digit is 80%)
            
            digitMask = digitMask[crop:-crop, crop:-crop]
#            plt.imshow(digitMask, cmap='binary')
#            plt.show()
        
        return digitMask
        
        
    
    def straightenAndStretchImage(self, mask, origImage):
        #1) uses mask of the soduku grid to find grid lines. Then rotates original image to so that top is horizontal.
        #2) next uses lines to find grid corners and stretches grid to fit full image
        
        #1)
        #imageEdges = cv2.Canny(mask, 100, 100, apertureSize=3)
        #use cv2 hough lines method to find lines within the image
        minLength=mask.shape[0]//5  #set min line length to 1/5 of image size.
        lines = cv2.HoughLinesP(mask, 1, math.pi / 180.0, 100, minLineLength=minLength, maxLineGap=5)
        
        hAngles = []
        vAngles = []
        
        #iterate through lines, find their angle, and sort into appropriate array
        for line in lines:
            for x1, y1, x2, y2 in line:
                angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                if angle < 45 and angle > -45:
                    hAngles.append(angle)
                if angle < 135 and angle >= 45:
                    vAngles.append(angle)
        
        #find median angle of horizontal lines
        medianAngle = np.median(hAngles)
        
        #rotate image to meet medianAngle of horizontal lines, fill new pixels with median of image pixel values
        rotatedImage = ndimage.rotate(origImage, medianAngle, cval = np.percentile(origImage, 50))
        rotatedMask = ndimage.rotate(mask, medianAngle, cval = 0)
        
        #2) finding grid corners
        
        #recompute image edges on rotated image
        dst = cv2.cornerHarris(rotatedMask,5,3,0.04)
        ret, dst = cv2.threshold(dst,0.1*dst.max(),255,0)
        dst = np.uint8(dst)
        ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dst)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
        corners = cv2.cornerSubPix(rotatedMask,np.float32(centroids),(5,5),(-1,-1),criteria)
        
        y, x = rotatedMask.shape
        imageCorners = np.array([[0,0],[0, x],[y,0],[y, x]])
        
        #top Left
        TLcorner = corners[np.argsort([math.sqrt(((imageCorners[0] - corner)**2).sum()) for corner in corners])[0]]
        TRcorner = corners[np.argsort([math.sqrt(((imageCorners[1] - corner)**2).sum()) for corner in corners])[0]]
        BLcorner = corners[np.argsort([math.sqrt(((imageCorners[2] - corner)**2).sum()) for corner in corners])[0]]
        BRcorner = corners[np.argsort([math.sqrt(((imageCorners[3] - corner)**2).sum()) for corner in corners])[0]]
        
        pts1 = np.float32([TLcorner,BLcorner,TRcorner,BRcorner])
        pts2 = np.float32([[0,0],[900,0],[0,900],[900,900]])
        M = cv2.getPerspectiveTransform(pts1,pts2)
        
        # warp image and mask to fit the grid exactly
        finalImage = cv2.warpPerspective(rotatedImage,M,(900,900))
        finalMask = cv2.warpPerspective(rotatedMask,M,(900,900))
        
        return (finalImage, finalMask)
    
    
    def extractDigitImages(self, gridImage, gridMask):
        
        cellDigitsDict = {}
        cellSize = 100
        for idy, row in enumerate(range(0,gridImage.shape[0], cellSize)):
            for idx, col in enumerate(range(0,gridImage.shape[1], cellSize)):
                #separate the sudoku image and grid mask into individual cells
                cellImage = gridImage[row:row+cellSize, col:col+cellSize]
                cellMask = gridMask[row:row+cellSize, col:col+cellSize]
                
                #use adaptive threshold to highlight the contours in the image
                cellImage = cv2.adaptiveThreshold(cellImage,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
                                            cv2.THRESH_BINARY_INV,21,4)
                
                #pass cell image and the grid mask to the createDigitMask for it to identify whether
                #the cell contains a digit
                digitMask = self.createDigitMask(cellImage, cellMask)
                
                #if a digit is found in the cell, resize the mask to (28,28) and
                #save it to the image Dictionary with its row and column
                if digitMask is not None:
                    digitMask = cv2.resize(digitMask, (28, 28), interpolation=cv2.INTER_AREA)
#                    plt.imshow(digitMask)
#                    plt.show()
                    cellDigitsDict[idy*10 + idx] = digitMask
                
        return cellDigitsDict
    
    def predictDigitValues(self, digitDict):
        #create list of images to be predicted
        digitImages = np.array([j for (i, j) in digitDict.items()])
        gridIndexes = [i for (i, j) in digitDict.items()]
        #add fourth dimension for color
        digitImages = digitImages.reshape(-1,28,28,1)
        imagePredictions = []
        

        #prevent Keras model conflicts caused by Flask threads
        with self.graph.as_default():
            with self.session.as_default():
                #load digit recognition model
                convnet = load_model('sudokuApp/trainedModels/DigitRecogConvnetRev2.h5')
                #convnet = load_model('gs://sudoku-image-solver/DigitRecogConvnetRev2.h5')
                imagePredictions = convnet.predict(digitImages)
                
        #create sudoku grid to store predictedd digits
        gridEntries = np.zeros((9,9)).astype(int)
        
        #created dictionary to hold the digit probabilities for each cell, in case they need to be reconsidered
        digitProbabilities = {}
        
        for idx, predictVector in enumerate(imagePredictions):
            #print('({},{}) = {}'.format(gridIndexes[idx]//10,gridIndexes[idx]%10,predictVector.argmax()))
            predictedDigit = predictVector.argmax()
            
            #if the convet predicts the digit to be zero, choose the digit with the next highest probability
            if predictedDigit == 0: 
                predictedDigit = np.argsort(predictVector)[::-1][1]
            
            gridEntries[gridIndexes[idx]//10,gridIndexes[idx]%10] = predictedDigit
            digitProbabilities[gridIndexes[idx]] = predictVector
        
        return (gridEntries, digitProbabilities)        
        
    def getPredictedGrid(self):
        #
        #
        #
        #check that image has been loaded
        return self.predictedGrid
    
    def getValueProbabilities(self):
        #
        #
        #
        #check that image has been loaded
        pass
    def printGrid(self):
        for r in range(9):
            print('\n|', end = '')
            for c in range(9):
                digit = self.predictedGrid[r,c]
                if digit == 0:
                    print(' |',end = '')
                else:
                    print(str(digit)+'|',end = '')
        print()
    
    def printImagesToFile(self, xGroups):
        all_data = np.hstack(yPredicts, xGroups)
        all_data = np.vstack()
        all_data = np.concatenate()
        
        np.save(file, array)
    
    def getDigitsDict(self):
        if self.digitsDict is not None:
            return self.digitsDict
        
if __name__ == '__main__':
    image = cv2.imread('static\\siteImages\\default.jpg')
    imProcessor = sudokuImageProcessor(image)
    imProcessor.printGrid()
    
    
    
    
    
    
    