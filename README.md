# Cash-Detection-MobileNetV2-Mscoco
This Project Scan a real time Video (Sequence of frames) ,creates a boundry on the identifed object and then labels accordingly. In this project an Object Detection API model based on SSD-MobilNetV2 and pre-trained on Mscoco dataset, was used to retrain on three Categories of cash items. Since a one-time detection is never reliable in case of low powered devices (With low processing frame rates) , the cash identified was left to be rescaned a number of times and then labled according to dominant output.

# Pre-requisite
OpenCV, Pretained Model(Preferably ; SSD-MobileNetV2), Tensorflow Object Detection API , Python 3.6 
