'''
This script plays the camera using the calibration parameters
It also lets the user click in a pixel and receive the x,y values
This script is just for testing. Not used in the final product
'''

import cv

def mouseHandler(event, x, y, flags, param):
	if event == cv.CV_EVENT_LBUTTONDOWN:
		print x,y

capture=cv.CaptureFromCAM(1)
image=cv.QueryFrame(capture)

intrinsic = cv.Load("Intrinsics.xml")
distortion = cv.Load("Distortion.xml")

mapx = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
mapy = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
cv.InitUndistortMap(intrinsic,distortion,mapx,mapy)
cv.NamedWindow( "Undistort" )
#cv.NamedWindow( "Original" )

clicks = 0 # after 6 clicks, calibration and then follow click
cv.SetMouseCallback("Undistort", mouseHandler, 1)

while(1):
	image=cv.QueryFrame(capture)
	t = cv.CloneImage(image);
	#cv.ShowImage( "Original", image )
	cv.Remap( t, image, mapx, mapy )
	cv.Flip(image,image,1)
	cv.ShowImage("Undistort", image)
	c = cv.WaitKey(10)
	if(c == 1048688):		# enter 'p' key to pause for some time
		cv.WaitKey(2000)
	elif c==1048603:		# enter esc key to exit
		break
