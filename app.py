import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Restrict TensorFlow to only use the fourth GPU
        tf.config.experimental.set_visible_devices(gpus[0], 'GPU')

        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)

# import necessary libraries
import cv2
import matplotlib.pyplot as plt
import numpy as np
import copy
import time
from tensorflow import keras
from tensorflow.keras import layers
import pyautogui
from PIL import Image
import time

# You can change the parameters down below according to your system and webcam
font = cv2.FONT_HERSHEY_SIMPLEX
dataColor = (0,0,255)
x1 = 50
y1 = 50
w = 200
p = 10
MogThreshold = 15
GuassianKernelSize = 11
ThreshValue = 5

#Parameters
fgbg = cv2.createBackgroundSubtractorMOG2(0,MogThreshold)
takingData = False

# create a function to apply  background mask
def bgMask(img):
    global fgbg
    fgmask = fgbg.apply(img)
    result = cv2.bitwise_and(img, img, mask=fgmask)
    return result
#create a function to apply GaussianBlur
def guassianBlurFun(img):
    global GuassianKernelSize
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (GuassianKernelSize,GuassianKernelSize), 100)
    return blur
# create a function to apply threshold
# If pixel value is smaller than the threshold set to 0, otherwise set to 1
def thresholdFun(img):
    global ThreshValue
    ret, thresh = cv2.threshold(img, ThreshValue, 255, cv2.THRESH_BINARY)
    return thresh


def main():
    global takingData, dataColor, font, x1, y1, w, p
    
    # Loading CNN model
    model = tf.keras.models.load_model('trained_model.h5')
    # I've passed parameter 1 in order to use external webcam,
    # IF you use internal webcam you should cahnge it to 0
    cap = cv2.VideoCapture(1) 
   
    while True:
        ret,frame = cap.read()
        frame = cv2.flip(frame, 1)
        cv2.rectangle(frame,(x1,y1),((x1+w),(y1+w)),dataColor,3)
        
        #Region of Intrest (inside rectangle frame)
        roi = frame[y1:(y1+w),x1:(x1+w)]
        
        #Background
        res = bgMask(roi)
        cv2.imshow('fgmask',res)

        #guassian
        blur = guassianBlurFun(res)
        cv2.imshow('guassian',blur)
        
        #threshold
        thresh = thresholdFun(blur)
        cv2.imshow('thresh',thresh)

        
        #Contours
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        length = len(contours)
        maxArea = -1
        if length > 0:
            # find the biggest contour, according to area
            for i in range(length): 
                temp = contours[i]
                area = cv2.contourArea(temp)
                if area > maxArea:
                    maxArea = area
                    ci = i

            res = contours[ci]
            hull = cv2.convexHull(res)
            drawing = np.zeros(roi.shape, np.uint8)
            cv2.drawContours(drawing, [res], 0, (0, 255, 0), 2)
            cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 3)
        cv2.imshow('main',drawing)
        
        
        # Convert frame to np.array so that can be used in CNN algorithm 
        img = Image.fromarray(drawing)
        img = img.resize((100,100))
        img_arr = np.array(img, np.float)
        img_arr = np.expand_dims(img_arr, axis =0)
        
        # Prediction and action 
        if takingData:
            dataColor = (0,255,0)
            cv2.putText(frame, 'Data Taking: ON', (5,20), font, 0.5, dataColor, 2, 1)
            result = model.predict(img_arr)
            if result[0][0] == 1:
                predictions = 'Jump'
                pyautogui.press('space')
            else:
                predictions = 'Not Jump'
            cv2.putText(frame, 'Predection: {}'.format(predictions), (x1,y1-10), font, 0.7, dataColor, 2, 1)
        else:
            dataColor = (0,0,255)
            cv2.putText(frame, 'Data Taking: OFF', (5,20), font, 0.5, dataColor, 2, 1)
        
        
        ## Show the main frame
        cv2.imshow('Original',frame)
        
        ##Toggle Keys##
        key = cv2.waitKey(1) & 0xFF
        # press '.' to close the app
        if key == ord('.'):
            break
        # press 's' to start prediction
        elif key == ord('s'):
            takingData = not takingData
        # press 'z' to narrow frame
        elif key == ord('z'):
            w = w + p
        # press 'q' to expand frame
        elif key == ord('q'):
            w = w - p
        # press 'l' to swipe frame right
        elif key == ord('l'):
            x1 = x1 + p
        # press 'l' to swipe frame left
        elif key == ord('j'):
            x1 = x1 - p
        # press 'l' to swipe frame down
        elif key == ord('k'):
            y1 = y1 + p
        # press 'l' to swipe frame up
        elif key == ord('i'):                                                 
            y1 = y1 - p
        
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()