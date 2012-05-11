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

class TMSolver():

	def __init__(self, p):

		self.p = p
		time.sleep(3)
		self.p.send_now("M43 P1 S180") #move the syringe to 180
		time.sleep(3)
		self.p.send_now("G28") #homing
		time.sleep(2)
		self.p.send_now("GM43 P0 S0") #homing
		time.sleep(1)
		self.p.send_now("GM43 P2 S0") #homing
		time.sleep(1)
		self.p.send_now("GM43 P4 S0") #homing
		time.sleep(1)
		self.p.send_now("GM43 P5 S0") #homing
		time.sleep(1)

		capture = cv.CaptureFromCAM(1)
		image = cv.QueryFrame(capture)

		intrinsic = cv.Load("/Users/joanmanel/Documents/thesis/TrackingDrops/CamCalibration/Intrinsics.xml")
		distortion = cv.Load("/Users/joanmanel/Documents/thesis/TrackingDrops/CamCalibration/Distortion.xml")

		mapx = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
		mapy = cv.CreateImage( cv.GetSize(image), cv.IPL_DEPTH_32F, 1 );
		cv.InitUndistortMap(intrinsic,distortion,mapx,mapy)
		cv.NamedWindow( "Undistort" )

		cv.SetMouseCallback("Undistort", self.mouseHandler, 0)

		self.clicks = 1
		self.tp = [245,43,252,49,261,57] # different tool positions. right now is static
		self.pixels = []
		self.alpha = 0 # rotation angle, to be calculated
		self.tx = 0 # translation over x, to be calculated
		self.ty = 0 # translation over y, to be calculated
		self.sx = 0 # scaling factor over x
		self.sy = 0 # scaling factor over y

		self.p.send_now("G1 X245 Y43 F10000") #MOVE TO THIS POSITION
		self.p.send_now("P4 G500") # WAIT 0.5S
		self.p.send_now("M43 P2 S55") # MOVE SYR DOWN

		while(1):
			image=cv.QueryFrame(capture)
			t = cv.CloneImage(image);
			cv.Remap( t, image, mapx, mapy )
			cv.Flip(image,image,1)
			cv.ShowImage("Undistort", image)
			c = cv.WaitKey(10)
			if self.tx > 0 or self.ty > 0:		# enter 'q' key to exit
				break 

		self.p.send_now("M43 P2 S0")
		cv.DestroyWindow('Undistort')
		del(mapx)
		del(mapy)
		del(image)
		del(capture)


	def findScale(self, pixels, tp):
		
		sx1 = abs( (pixels[0]-float(pixels[2])) / (tp[0]-tp[2]) )
		sx2 = abs( (pixels[2]-float(pixels[4])) / (tp[2]-tp[4]) )
		sx3 = abs( (pixels[4]-float(pixels[0])) / (tp[4]-tp[0]) )

		sy1 = abs( (pixels[1]-float(pixels[3])) / (tp[1]-tp[3]) )
		sy2 = abs( (pixels[3]-float(pixels[5])) / (tp[3]-tp[5]) )
		sy3 = abs( (pixels[5]-float(pixels[1])) / (tp[5]-tp[1]) )

		return (sx1+sx2+sx3)/3., (sy1+sy2+sy3)/3.

	def trigLinearSolver(self, a,b,c):
		''' solving the linear combination of sin and cos '''
		if a < 0:
			a = a * -1
			b = b * -1
			c = c * -1
		u = asin( b / sqrt( a**2 + b**2 ) )
		return asin( -c / sqrt( a**2 + b**2 ) ) - u

	def findAlpha(self, pixels, tp):
		# first pair
		# solving for tx
		a = pixels[1] - pixels[3]
		b = -pixels[0] + pixels[2]
		c = tp[0] - tp[2]
		alpha1 = self.trigLinearSolver(a,b,c)

		# solving for ty
		a = -pixels[0] + pixels[2]
		b = -pixels[1] + pixels[3]
		c = tp[1]-tp[3]
		alpha2 = self.trigLinearSolver(a,b,c)

		# second pair
		# solving for tx
		a = pixels[3] - pixels[5]
		b = -pixels[2] + pixels[4]
		c = tp[2] - tp[4]
		alpha3 = self.trigLinearSolver(a,b,c)

		# solving for ty
		a = -pixels[2] + pixels[4]
		b = -pixels[3] + pixels[5]
		c = tp[3]-tp[5]
		alpha4 = self.trigLinearSolver(a,b,c)

		return ( alpha1 + alpha2 + alpha3 + alpha4 ) / 4.0


	def findTMatrix(self, pixels, tp ):
		'''solving the TM matrix for a pair of points, and using the linear combination of sin and cos'''
		
		alpha = self.findAlpha( pixels, tp)
		tx1 = tp[0] -cos(alpha)*pixels[0] + sin(alpha)*pixels[1]
		ty1 = tp[1] -sin(alpha)*pixels[0] - cos(alpha)*pixels[1]

		tx2 = tp[2] -cos(alpha)*pixels[2] + sin(alpha)*pixels[3]
		ty2 = tp[3] -sin(alpha)*pixels[2] - cos(alpha)*pixels[3]

		return alpha, (tx1+tx2)/2.0, (ty1+ty2)/2.0

	def mouseHandler(self, event, x, y, flags, param):

		if event == cv.CV_EVENT_LBUTTONDOWN:

			self.pixels.append(x)
			self.pixels.append(y)

			if self.clicks < 3:
				command = 'G1 X%d Y%d F10000' % ( self.tp[(self.clicks*2)], self.tp[(self.clicks*2)+1] )
				self.p.send_now(command)
				time.sleep(1)
				self.clicks = self.clicks + 1

			else: # self.clicks == 3:
				self.sx,self.sy = self.findScale(self.pixels, self.tp)
				self.pixels = [ self.pixels[0]/self.sx, self.pixels[1]/self.sy, self.pixels[2]/self.sx, 
					self.pixels[3]/self.sy, self.pixels[4]/self.sx, self.pixels[5]/self.sy ]
				self.alpha, self.tx, self.ty = self.findTMatrix( self.pixels, self.tp)
				self.clicks = self.clicks + 1

if __name__ == "__main__":

	sleep(3)
	p = printcore.printcore("/dev/tty.usbserial-A4008eY6",115200)
	sleep(3)
	#p.loud=True

	solver = TMSolver(p)
	print "scaling factor sx sy ", solver.sx, solver.sy
	print "angle ", solver.alpha
	print "translation over x and y", solver.tx, solver.ty
