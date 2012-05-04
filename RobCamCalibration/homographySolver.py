import cv
import cv2
import time
import numpy as np
from random import uniform

def mouseHandler(event, x, y, flags, param):

	global pixels
	global tool_position
	global H
	global clicks

	if event == cv.CV_EVENT_LBUTTONDOWN:
		clicks = clicks + 1
		pixels.append(x/13.)
		pixels.append(y/12.5)
		a = np.array(pixels, np.float32).reshape(-1,2)
		b = np.array(tool_position, np.float32).reshape(-1,2)
		if clicks > 3:
			H,matches = cv2.findHomography(a, b, cv2.RANSAC)
			print H
		xrob = uniform(250,280)
		yrob = uniform(25,45)
		command = 'G1 X%d Y%d F10000' % (xrob,yrob)
		p.send_now(command)
		tool_position.append(xrob)
		tool_position.append(yrob)


import printcore
p=printcore.printcore("/dev/tty.usbserial-A4008eY6",115200)
time.sleep(5)
p.send_now("M43 P1 S50")
time.sleep(5)
p.send_now("G28") #homing
time.sleep(5)


capture=cv.CaptureFromCAM(1)
image=cv.QueryFrame(capture)

intrinsic = cv.Load("../CamCalibration/Intrinsics.xml")
distortion = cv.Load("../CamCalibration/Distortion.xml")

mapx = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
mapy = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
cv.InitUndistortMap(intrinsic,distortion,mapx,mapy)
cv.NamedWindow( "Undistort" )

pixels = []
clicks = 0
tool_position = [] # different tool positions. right now is static
H = np.array([]) # to store the homography matrix
cv.SetMouseCallback("Undistort", mouseHandler, 0)

p.send_now("G1 X280 Y25 F10000")
tool_position.append(280)
tool_position.append(25)

while(1):
	image=cv.QueryFrame(capture)
	t = cv.CloneImage(image);
	cv.Remap( t, image, mapx, mapy )
	cv.Flip(image,image,1)
	cv.ShowImage("Undistort", image)
	c = cv.WaitKey(10)
