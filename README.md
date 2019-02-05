# pi-cam
Remote camera system that uses computer vision to keep track of objects. 
(Note that the API Keys have been removed, so the system won't be able to connect to the database)

# Python Script
Python script is meant to run on a Raspberry Pi with a camera module (although it could be modified to work with a webcam). It uses a pre-trained neural network model to detect objects in real-time and update the Firebase Database accordingly. It also listens for changes on the parameters set by the user on the website.

# Website
Upon entering a valid username, it retrieves the information from the camera(s) set up by the user. It gets the information in real-time from the Firebase Database. It also allows the user to change parameters such as what object to detect, minimum confidence, as well as switching the camera on and off. Finally, it allows the user to download a file containing all the information processed by each camera.

You can see the website @ https://my-pi-cam.firebaseapp.com/
