'''
This code solves the transformation matrix between camera frame and robot frame.
It's a 2D transformation matrix, so we have to solve translation over x, y and angle alpha.
Just 2 pair of points are enough to solve the equations, we are using 3 for... robustness.
The transformation matrix we are considering is as follows, where a is alpha:

| cos(a) -sin(a) tx |
| sin(a)  cos(a) ty |
|   0      0      1 |

With just 1 camera we cannot do a 3D reconstruction. The scaling factor is ommited and calculated
with just the points not inside TM, otherwise we would have 5 unknown variables that would require more points
and a madness of equations to solve. The results are not as precisse, but we think they are.. precisse enough.
'''

from math import sqrt, asin, sin, cos
import time

import cv
import printcore

def findScale(pixels, tp):
	
	sx1 = abs( (pixels[0]-float(pixels[2])) / (tp[0]-tp[2]) )
	sx2 = abs( (pixels[2]-float(pixels[4])) / (tp[2]-tp[4]) )
	sx3 = abs( (pixels[4]-float(pixels[0])) / (tp[4]-tp[0]) )

	sy1 = abs( (pixels[1]-float(pixels[3])) / (tp[1]-tp[3]) )
	sy2 = abs( (pixels[3]-float(pixels[5])) / (tp[3]-tp[5]) )
	sy3 = abs( (pixels[5]-float(pixels[1])) / (tp[5]-tp[1]) )

	return (sx1+sx2+sx3)/3., (sy1+sy2+sy3)/3.

def trigLinearSolver(a,b,c):
	''' solving the linear combination of sin and cos '''
	if a < 0:
		a = a * -1
		b = b * -1
		c = c * -1
	print a,b,c
	u = asin( b / sqrt( a**2 + b**2 ) )
	return asin( -c / sqrt( a**2 + b**2 ) ) - u

def findAlpha(pixels, tp):
	print pixels, tp
	# first pair
	# solving for tx
	a = pixels[1] - pixels[3]
	b = -pixels[0] + pixels[2]
	c = tp[0] - tp[2]
	alpha1 = trigLinearSolver(a,b,c)

	# solving for ty
	a = -pixels[0] + pixels[2]
	b = -pixels[1] + pixels[3]
	c = tp[1]-tp[3]
	alpha2 = trigLinearSolver(a,b,c)

	# second pair
	# solving for tx
	a = pixels[3] - pixels[5]
	b = -pixels[2] + pixels[4]
	c = tp[2] - tp[4]
	alpha3 = trigLinearSolver(a,b,c)

	# solving for ty
	a = -pixels[2] + pixels[4]
	b = -pixels[3] + pixels[5]
	c = tp[3]-tp[5]
	alpha4 = trigLinearSolver(a,b,c)

	return ( alpha1 + alpha2 + alpha3 + alpha4 ) / 4.0


def findTMatrix( pixels, tp ):
	'''solving the TM matrix for a pair of points, and using the linear combination of sin and cos'''
	
	alpha = findAlpha( pixels, tp)
	tx1 = tp[0] -cos(alpha)*pixels[0] + sin(alpha)*pixels[1]
	ty1 = tp[1] -sin(alpha)*pixels[0] - cos(alpha)*pixels[1]

	tx2 = tp[2] -cos(alpha)*pixels[2] + sin(alpha)*pixels[3]
	ty2 = tp[3] -sin(alpha)*pixels[2] - cos(alpha)*pixels[3]

	return alpha, (tx1+tx2)/2.0, (ty1+ty2)/2.0

def mouseHandler(event, x, y, flags, param):

	global tp, pixels, clicks, alpha, tx, ty, sx, sy
	global pixels
	global clicks

	if event == cv.CV_EVENT_LBUTTONDOWN:

		pixels.append(x)
		pixels.append(y)

		if clicks < 3:
			command = 'G1 X%d Y%d F10000' % ( tp[(clicks*2)], tp[(clicks*2)+1] )
			p.send_now(command)
			clicks = clicks + 1

		elif clicks == 3:
			sx,sy = findScale(pixels, tp)
			pixels = [ pixels[0]/sx, pixels[1]/sy, pixels[2]/sx, pixels[3]/sy, pixels[4]/sx, pixels[5]/sy ]
			alpha, tx, ty = findTMatrix( pixels, tp)
			clicks = clicks +1
		else:
			robx = (x/sx) * cos(alpha) - (y/sy) * sin(alpha) + tx
			roby = (x/sx) * sin(alpha) + (y/sy) * cos(alpha) + ty
			command = 'G1 X%d Y%d F10000' % ( robx, roby )
			p.send_now(command)



p=printcore.printcore("/dev/tty.usbserial-A4008eY6",115200)
#p.loud=True
time.sleep(5)
p.send_now("M43 P1 S50") #move the syringe to 100
time.sleep(5)
p.send_now("G28") #homing
time.sleep(5)

capture=cv.CaptureFromCAM(1)
image=cv.QueryFrame(capture)

intrinsic = cv.Load("Intrinsics.xml")
distortion = cv.Load("Distortion.xml")

mapx = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
mapy = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
cv.InitUndistortMap(intrinsic,distortion,mapx,mapy)
cv.NamedWindow( "Undistort" )

cv.SetMouseCallback("Undistort", mouseHandler, 0)

clicks = 1
tp = [257,27,267,32,281,42] # different tool positions. right now is static
pixels = []
alpha = 0 # rotation angle, to be calculated
tx = 0 # translation over x, to be calculated
ty = 0 # translation over y, to be calculated
sx = 0 # scaling factor over x
sy = 0 # scaling factor over y

p.send_now("G1 X257 Y27 F10000")

while(1):
	image=cv.QueryFrame(capture)
	t = cv.CloneImage(image);
	cv.Remap( t, image, mapx, mapy )
	cv.Flip(image,image,1)
	cv.ShowImage("Undistort", image)
	c = cv.WaitKey(10)
	if c == 'q':		# enter 'q' key to exit
		break 