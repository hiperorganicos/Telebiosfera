# Adapted by: George Rappel <george.concei[at]hotmail.com>
# From: http://pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
#
#  Functionality: IP updated automatically by Free DNS service.
#  Adress: {freedns domain. ex: shast.ignorelist.com}:7777/video_feed
# =========================================================

# import the necessary packages
import sys
sys.path.append('/usr/local/lib/python2.7/dist-packages')

import argparse
import datetime
from OSC import OSCClient, OSCMessage
import cv2
import imutils
import time
import Queue
import threading
from flask import Flask, render_template, Response
import multiprocessing
import subprocess
from picamera.array import PiRGBArray
from picamera import PiCamera
from picamera import PiCameraValueError

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import StringIO


# Create the haar cascade
faceCascade = cv2.CascadeClassifier("lbpcascade_frontalface.xml") #Faster
#faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_alt_tree.xml")


manager = multiprocessing.Manager()
q = manager.Queue(5)

showVideo = True

# Update shastcam.ignorelist.com DNS (public static IP)
def updateDNS():
    subprocess.call(["bash", "update_freedns.sh"])
    print ("DNS Updated.")

# ========================================================================
# Thread & Flask
# ========================================================================
def camrunner(q):

    queu = q

    class CamHandler(BaseHTTPRequestHandler):
        queue = None
        def do_GET(self):
            if self.path.endswith('.mjpg'):
                self.send_response(200)
                self.send_header('Content-type','multipart/x-mixed-replace; boundary=frame')
                self.end_headers()
                while True:
                    try:
                        if not self.queue.empty():
                            frame = None
                            frameaux = self.queue.get()
                            if frameaux is not None:
                                ret, jpeg = cv2.imencode('.jpeg', frameaux)
                                frame = jpeg.tostring()

                            self.wfile.write("--frame")
                            self.send_header('Content-type','image/jpeg')
                            self.wfile.write('\r\n' + frame)
                            self.end_headers()
                            time.sleep(0.04) #slow the stream a bit (framerate)
                        else:
                            print("queue vazia")
                    except KeyboardInterrupt:
                        break
                return
            else:
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<html><head></head><body>')
                self.wfile.write('<img src="/cam.mjpg"/>')
                self.wfile.write('</body></html>')
                return

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        """Handle requests in a separate thread."""

    def main(queuee):
        try:
            camhand = CamHandler
            camhand.queue = queuee
            server = ThreadedHTTPServer(('0.0.0.0', 8080), camhand)
            print ("server started")
            server.serve_forever()
        except KeyboardInterrupt:
            capture.release()
            server.socket.close()

    if __name__ == '__main__':
        main(queu)
# ========================================================================
# OSC CLIENT AND FUNCTIONS
# ========================================================================
timeLastConnection = 0
client = OSCClient()

def connectOsc():
    global client, timeLastConnection
    if timeLastConnection < time.time() - 7200: # Reconnect every two hours
        print("connecting to OSC server")
        updateDNS()
        client = OSCClient()
        client.connect( ("146.164.80.56", 22244) )
        timeLastConnection = time.time()

connectOsc()

def sendOscMessage(_x, _y, _w, _h):
    if x > 1 and y > 1:
        global client
        connectOsc()
        msg = OSCMessage("/shast/coordenadas")
        msg.extend([_x, _y, _w, _h])
        client.send( msg )

# =======================================================================
# Motion detection
# =======================================================================

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-a", "--min-area", type=int, default=300, help="minimum area size")
args = vars(ap.parse_args())

# Reading from Raspicam
camera = PiCamera(resolution=(320, 240), framerate=32)
rawCapture = PiRGBArray(camera, size=(320, 240))
time.sleep(0.1)
# initialize the first frame in the video stream
firstFrame = None

# Regulate the OSC stream to send only every other frame
otherFrame = False

# Start Flask
print("Starting stream server...")
p = multiprocessing.Process(target=camrunner, args=(q,))
p.daemon = True
p.start()
print("Started stream!")
# loop over the frames of the video
print("Starting image reading...")
#while True:

def nothing(*arg):
    pass

#cv2.namedWindow('edge')
#cv2.createTrackbar('thrs1', 'edge', 2000, 5000, nothing)
#cv2.createTrackbar('thrs2', 'edge', 4000, 5000, nothing)


for imagetkn in camera.capture_continuous(rawCapture, format="bgr", splitter_port=1, use_video_port=True):
    timestart = time.time()   
    try:
        frame = imagetkn.array
        rawCapture.truncate(0)
        if frame is None:
            print("is none")
            continue
        frame = imutils.resize(frame, width=400)
        # Coloca o frame redimensionado na Queue
        if not q.full() and frame is not None:
            q.put_nowait(frame)

        # Convert the frame to grayscale, and blur it
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        print("--Bef: ", time.time()-timestart)

        # Detect faces in the image
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1,
                minNeighbors=5, minSize=(50, 50) #flags = cv2.CV_HAAR_SCALE_IMAGE
        )
        
        print("--Aft: ", time.time()-timestart)
        #print("Found {0} faces!".format(len(faces)))

        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            #sendOscMessage(x, y, w, h)

        # show the frame and record if the user presses a key
        # opens three video windows
        if showVideo:
            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # draw the text and timestamp on the frame
            cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            cv2.imshow("Security Feed", frame)
            #cv2.imshow("Canny", cv2.Canny(frame, 2000, 4000, apertureSize=5))
    except PiCameraValueError as err:
        print("Exception PiCameraValueError ", err)


    key = cv2.waitKey(1) & 0xFF

    # if the `q` key is pressed, break from the lop
    if key == ord("q"):
        break
    print("End: ", time.time()-timestart)
    print("")
    # give the PC (and OSC server) some time to breathe
    #time.sleep(0.1)

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
