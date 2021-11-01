#import send_string_to_arduino
#import serial

import os
import cv2
import numpy as np
import tensorflow as tf
import sys
import time
import RPi.GPIO as GPIO
import globals

# This is for LED,IR and motor setup 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) # setup Pi with board-pin numbering

IR1 =7
IR2 = 11
RED = 13 
GREEN = 15
LED = 40
EN = 22
IN1 = 16
IN2 = 18

GPIO.setup(IR1,GPIO.IN) #board pin 7 -> IR sensor as input
GPIO.setup(IR2,GPIO.IN) #board pin 11 -> IR sensor as input

GPIO.setup(RED,GPIO.OUT) #board pin 13 -> Red LED as output
GPIO.setup(GREEN,GPIO.OUT) #board pin 15-> Green LED as output
GPIO.setup(LED,GPIO.OUT) #board pin 40 -> Lighting LED as output

GPIO.setup(EN,GPIO.OUT) #board pin 22 -> connect to L298N Enable 
GPIO.setup(IN1,GPIO.OUT) #board pin 16 -> connect to L298N IN1 
GPIO.setup(IN2,GPIO.OUT) #board pin 18 -> connect to L298N IN2

# RESET EVERY DIGITAL PIN 
GPIO.output(RED,GPIO.LOW)
GPIO.output(GREEN,GPIO.LOW)
GPIO.output(LED,GPIO.LOW)

GPIO.output(IN1,GPIO.LOW)
GPIO.output(IN2,GPIO.LOW)

# set our PWM pin up with a frequency of 1kHz, and set that output to a 50% duty cycle.
pwm = GPIO.PWM(EN,1000)


# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")

# Import utilites
from utils import label_map_util
from utils import visualization_utils as vis_util

# Name of the directory containing the object detection module we're using
MODEL_NAME = 'inference_graph'
VIDEO_NAME = 'test.mov'

# Grab path to current working directory
CWD_PATH = os.getcwd()

# Path to frozen detection graph .pb file, which contains the model that is used
# for object detection.
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,'frozen_inference_graph.pb')

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,'training','labelmap.pbtxt')

# Path to video
PATH_TO_VIDEO = os.path.join(CWD_PATH,VIDEO_NAME)

# Number of classes the object detector can identify
NUM_CLASSES = 3

# Load the label map.
# Label maps map indices to category names, so that when our convolution
# network predicts `2`, we know that this corresponds to `Rs10`.
# Here we use internal utility functions, but anything that returns a
# dictionary mapping integers to appropriate string labels would be fine
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Load the Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

    sess = tf.Session(graph=detection_graph)

# Define input and output tensors (i.e. data) for the object detection classifier

# Input tensor is the image
image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

# Output tensors are the detection boxes, scores, and classes
# Each box represents a part of the image where a particular object was detected
detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

# Each score represents level of confidence for each of the objects.
# The score is shown on the result image, together with the class label.
detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

# Number of objects detected
num_detections = detection_graph.get_tensor_by_name('num_detections:0')



# Make globla variables available to use
globals.init()

# Provided by arduino
print("\n","send any amount from DUE to trigger the following","\n")
print("------------------------------------------------------------------------")
bill = int(input("Enter total bill amount : Rs"))
print("------------------------------------------------------------------------")
 
while True:
    print("\n\t\t"," *** Rs.", (bill - globals.total_detected), " pending ***","\n")
    print("Put the cash in scanner to proceed ...","\n")
    # Wait till IR1 Detects/Reflects i.e. FALSE
    while(GPIO.input(IR1) == 1):
        # Green led for No money
        GPIO.output(GREEN,HIGH)
        GPIO.output(RED,GPIO.LOW)
        print("##### Cash Not Detected Yet #####","\t","-- ENTER CASH","\n")
        time.sleep(1)
    
    if(GPIO.input(IR1) == 0):
        print("##### Cash Detected #####","\n")
        # Motor pulls in Forward direction
        GPIO.output(IN1,GPIO.HIGH)
        GPIO.output(IN2,GPIO.LOW)
        # Note: Upon hindrance/reflection, the output pin gives out a digital signal (a low-level signal).
    print("Do you want to Proceed.....","\n")
    ans = input("[y/n] : ")
    if ans == 'y':
        # Red led for processing
        GPIO.output(GREEN,GPIO.LOW)
        GPIO.output(RED,GPIO.HIGH)
        Print("Proceeding to detection Phase.....","\n")

        pwm.start(0)# Start 0% speed
        x = 0
        while(GPIO.input(IR1) == 0):
            Print("Speed: ",x)
            pwm.ChangeDutyCycle(x)
            if(x>25): # start from 0 and maintain speed at 25
                x=x-1
            else:
                x = x + 1
            time.sleep(0.25)
                
        # Here we place cash below camera after it passes first IR
        
        for i in range(25): # max 40   
            Print("Speed: ",x)
            pwm.ChangeDutyCycle(x)
            # start from 40 and drop to 0
            if(x>0):x=x-1
            time.sleep(0.25)
            
        #Assuming the cash has been placed below camera
        pwm.stop()
        
        # Open video file
        # Start the vedio capture and lighting inside box
        GPIO.output(LED,GPIO.HIGH)
        time.sleep(0.2)
        video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        while(video.isOpened()):
            #setting time reference
            stime = time.time()
                
            # Acquire frame and expand frame dimensions to have shape: [1, None, None, 3]
            # i.e. a single-column array, where each item in the column has the pixel RGB value
            ret, frame = video.read()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_expanded = np.expand_dims(frame_rgb, axis=0)

            # Perform the actual detection by running the model with the image as input
            (boxes, scores, classes, num) = sess.run(
                [detection_boxes, detection_scores, detection_classes, num_detections],
                feed_dict={image_tensor: frame_expanded})

            # Draw the results of the detection (aka 'visulaize the results')
            vis_util.visualize_boxes_and_labels_on_image_array(
                frame,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index,
                use_normalized_coordinates=True,
                line_thickness=8,
                min_score_thresh=0.60)

            # All the results have been drawn on the frame, so it's time to display it.
            cv2.imshow('Object detector', frame)
            #display frame rate
            print('  -> Processing of Cash.No.',globals.iteration,'---------- with ---------- FPS {:.1f}'.format(1 / (time.time() - stime)))
                
            # Press 'q' to quit
            if cv2.waitKey(1) == ord('q'):# Note: important (line 122) needed to provide enough processing time for image to show in capture window 
                break

            #when the repeated result exceeds 10 then stop:
            if globals.count>=10:
                cash_detected = globals.temp1 # Storing the final decided value
                globals.count = 0
                globals.iteration += 1 
                break
                
        #Destroy capture and Turn OFF lighting
        video.release()
        cv2.destroyAllWindows()   
        GPIO.output(LED,GPIO.LOW)
        time.sleep(0.2)
        
        # Pull money by some fixed steps so that it reaches IR2
        pwm.start(25)
        for i in range(25):
            pwm.ChangeDutyCycle(25-i)
            time.sleep(0.05)
        
        # Drop the money using second IR
        while(GPIO.input(IR2) == False):
            pwm.ChangeDutyCycle(50)
            time.sleep(0.25)
        pwm.ChangeDutyCycle(50)
        pwm.stop()

        # Turn off leds after done processing
        GPIO.output(RED,GPIO.LOW)

        # Now counting Paid Cash Amount 
        sliced = cash_detected[2:]#removing "Rs" 
        intsliced=int(sliced)#converting remaining character to integer

        #display total amount paid till now 
        print("------------------------------------------------------------------------")
        print("\t\t\t\t\t",'Recent Paid Amount = Rs',intsliced)
        print("------------------------------------------------------------------------")
            
        #adding the cash to get total_detected sum
        globals.total_detected = globals.total_detected + intsliced
            
        if globals.total_detected >= bill:
            break

    elif ans == 'n':
        break
    else:
        print("\n","Error : **** only [y] or [n] is accepted ****","\n")        


#outside loop

#Clean Up GPI
GPIO.output(RED,GPIO.LOW)
GPIO.output(GREEN,GPIO.LOW)
GPIO.output(LED,GPIO.LOW)
GPIO.output(IN1,GPIO.LOW)
GPIO.output(IN2,GPIO.LOW)
GPIO.cleanup()

#display total sum
print("------------------------------------------------------------------------")
print("Bill :",bill,"Total Paid Amount ====> Rs",globals.total_detected)
print("------------------------------------------------------------------------")
# Clean up
video.release()
cv2.destroyAllWindows()
