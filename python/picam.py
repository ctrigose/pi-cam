# USAGE
# python picam.py -u [your username] -c [name for the cam]

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
from pivideostream import PiVideoStream
import numpy as np
import argparse
import imutils
from pyrebase import pyrebase
import datetime
import time
import cv2
import json

try:
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--username", required=True,
                    help="enter your username")
    ap.add_argument("-c", "--cam_id", required=True,
                    help="name of the camera")

    args = vars(ap.parse_args())

    date = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
    account = {
        "username": "",
        "cam_id": ""
    }
    data = {
        "people": 0,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    status = "offline"
    detections_dict = {"date": date}
    counter = 0
    db_confidence = 0.4
    current_detection = {
        "obj": "none",
        "confidence": 0,
        "time": "n/a"
    }

    # FIREBASE DATABASE CONFIGURATION

    config = {
        "apiKey": "", 
        "authDomain": "my-pi-cam.firebaseapp.com",
        "databaseURL": "https://my-pi-cam.firebaseio.com/",
        "storageBucket": "my-pi-cam.appspot.com",
    }

    firebase = pyrebase.initialize_app(config)

    db = firebase.database()

    def setup_cam():

        global account
        global db_confidence

        username = args["username"]
        cam_id = args["cam_id"]
        account = {
            "username": username,
            "cam_id": cam_id
        }

        db_confidence = 0.4

        setup_data = {
            "info": {
                "detect": "person",
                "status": "offline",
                "people": "N/A",
                "time": "N/A",
                "min_confidence": db_confidence
            },
            "all-data": {
                username: cam_id
            }
        }

        db.child(args["username"]).child(args["cam_id"]).update(setup_data)

        print(setup_data)


    setup_cam()

    # initialize the list of class labels MobileNet SSD was trained to
    # detect, then generate a set of bounding box colors for each class
    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
               "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
               "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
               "sofa", "train", "tvmonitor"]
    COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

    all_obj_count = {
        "background": 0
    }

    for k in range(13):
        all_obj_count.update({CLASSES[k]: 0})

    # load our serialized model from disk
    print("[INFO] loading model...")
    net = cv2.dnn.readNetFromCaffe("/home/pi/Desktop/obj_det/MobileNetSSD_deploy.prototxt.txt",
                                   "/home/pi/Desktop/obj_det/MobileNetSSD_deploy.caffemodel")

    # initialize the video stream, allow the cammera sensor to warmup,
    # and initialize the FPS counter
    print("[INFO] starting video stream...")
    vs = PiVideoStream().start()
    time.sleep(2.0)
    fps = FPS().start()

    frame_count = 0
    counter_ = 0
    detect = "person"

    # loop over the frames from the video stream
    while True:
        if status == "online":
            # grab the frame from the threaded video stream and resize it
            # to have a maximum width of 400 pixels
            frame = vs.read()
            frame = imutils.resize(frame, width=400)

            # grab the frame dimensions and convert it to a blob
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                         0.007843, (300, 300), 127.5)

            # pass the blob through the network and obtain the detections and
            # predictions
            net.setInput(blob)
            detections = net.forward()

            obj_count = 0
            # loop over the detections
            for i in np.arange(0, detections.shape[2]):
                # extract the confidence (i.e., probability) associated with
                # the prediction
                confidence = detections[0, 0, i, 2]

                # filter out weak detections by ensuring the `confidence` is
                # greater than the minimum confidence
                if confidence > db_confidence:
                    # extract the index of the class label from the
                    # `detections`, then compute the (x, y)-coordinates of
                    # the bounding box for the object
                    idx = int(detections[0, 0, i, 1])
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    # draw the prediction on the frame
                    label = "{}: {:.2f}%".format(CLASSES[idx],
                                                 confidence * 100)
                    cv2.rectangle(frame, (startX, startY), (endX, endY),
                                  COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(frame, label, (startX, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

                    if str(CLASSES[idx]) == str(detect):
                        obj_count += 1

                    current_detection={
                        "obj": CLASSES[idx],
                        "confidence": float("{0:.2f}".format(confidence)),
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    detections_dict.update(current_detection)

            frame_count=frame_count+1

            if obj_count != data["people"]:
                data.update({
                    "people": obj_count,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                db.child(args["username"]).child(
                    args["cam_id"]).child("info").update(data)
                db.child(args["username"]).child(args["cam_id"]).child(
                    "data").child(counter_).update(data)
                counter_ += 1

            if frame_count % 3 == 0:
                db_info=db.child(account["username"]).child(
                    account["cam_id"]).child("info").get()
                temp=db_info.val()
                db_confidence=temp["min_confidence"]
                status=temp["status"]
                detect=temp["detect"]
                '''for key, value in all_obj_count.items():
                    db.child(args["username"]).child(args["cam_id"]).child(
                        "all-data").child(key).set(value)'''
                print(status)

            # show the output frame
            cv2.imshow("Frame", frame)
            key=cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break

            # update the FPS counter
            fps.update()
            
        time.sleep(0.5)
        db_info=db.child(args["username"]).child(
            account["cam_id"]).child("info").get()
        temp=db_info.val()
        status=temp["status"]

    print('Interrupted')
    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    print("People found {:.2f}".format(data))
    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()
    detections_output="DETECTIONS: "
    for i in detections_dict:
        detections_output += i
    print(detections_output)

    with open("detections.txt ", 'w', encoding='utf-8') as outfile:
        json.dump(detections_output, outfile)

except Exception as e:
    cv2.destroyAllWindows()
    vs.stop()
    print(e)
