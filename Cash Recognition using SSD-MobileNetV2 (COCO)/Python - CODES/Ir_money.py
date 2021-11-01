import RPi.GPIO as GPIO
import time
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) # set up board pin numbering


GPIO.setup(4,GPIO.IN) #board pin 3 -> IR sensor as input
GPIO.setup(16,GPIO.OUT) #Gboard pin 16 -> Red LED as output
GPIO.setup(18,GPIO.OUT) #board pin 18 -> Green LED as output


while(1):
  if(GPIO.input(23)==True): #object is far away
        GPIO.output(2,True) #Red led ON
        GPIO.output(3,False) # Green led OFF
  if(GPIO.input(23)==False): #object is near
        GPIO.output(3,True) #Green led ON
        GPIO.output(2,False) # Red led OFF