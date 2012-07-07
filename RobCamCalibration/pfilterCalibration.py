from random import random, uniform
from math import sqrt
import time

import cv


class Condensation:

	def __init__(self, numParticles, iniTransX, iniTransY):

		self.numParticles = numParticles
		self.particles = []
		self.estimation = [0, 0, 0, 0]

		for i in range(numParticles):
			x = uniform( iniTransX - 5, iniTransX + 5 )
			y = uniform( iniTransY - 5, iniTransY + 5 )
			self.particles.append( Particle(x,y) )

	def reset(self, transx, transy):

		for particle in self.particles:
			x = uniform( transx - 2, transx + 2 )
			y = uniform( transy - 2, transy + 2 )
			particle.transX = x
			particle.transY = y

	def propagate(self, x, y, robx, roby):

		for particle in self.particles:
			particle.propagate(x,y,robx,roby)

	def updateWeights(self, x, y):

		for particle in self.particles:
			particle.calculateWeight(x, y)

		sum_weights = 0
		for particle in self.particles:
			sum_weights += particle.weight

		for particle in self.particles:
			particle.normWeight(sum_weights)

	def reSampling(self):

		temp_particles = []

		cumulative = [0] * (self.numParticles+1)
		
		for i in range(self.numParticles):
			cumulative[i+1] = cumulative[i] + self.particles[i].weight

		for i in range(self.numParticles):
			ranNum = random()
			k = 1
			while ranNum > cumulative[k]: 
				k+=1
			temp_particles.append( self.particles[k-1].copy() )

		while len(temp_particles) < self.numParticles:
			randParticle = int( uniform( 0, self.numParticles ) )
			temp_particles.append( self.particles[randParticle].copy() )

		self.particles = temp_particles


	def estimateState(self):

		x, y, tx, ty = 0, 0, 0, 0

		for particle in self.particles:
			x += particle.weight * particle.toolX
			y += particle.weight * particle.toolY
			tx += particle.weight * particle.transX
			ty += particle.weight * particle.transY

		self.estimation[0] = x
		self.estimation[1] = y
		self.estimation[2] = tx
		self.estimation[3] = ty


class Particle:

	def __init__(self, inX, inY):
		''' inX and inY are the translation, so the tool will be at x*cos(a)-y*sin(a)+inX=X
		and x*sin(a)+ycos(a)+inY=Y. In our case since a = -pi/2, cos(a)=-1 and sin(a)=0
		so X = -x+inX and Y = y+inY
		The filter will filter the translations over x and y, considering the angle static '''
		self.transX = inX
		self.transY = inY
		self.toolX = 1 * 0 + self.transX
		self.toolY = 1 * 0 +  self.transY
		self.weight = 0

	def copy(self):
		newParticle = Particle(self.transX, self.transY)
		newParticle.weight = self.weight
		newParticle.toolX = self.toolX
		newParticle.toolY = self.toolY
		return newParticle

	def propagate(self, x, y, robx, roby):

		ranDir = uniform(-1, 1)
		#ranDis = uniform(0, 2)
		self.transX -= x + self.transX - robx + ranDir
		self.transY -= y + self.transY - roby + ranDir
		self.toolX = x + self.transX
		self.toolY = y + self.transY


	def calculateWeight(self, x, y):

		self.weight = 1 / sqrt( (x-self.toolX)**2 + (y-self.toolY)**2)


	def normWeight(self, suma):

		self.weight = self.weight / float(suma)

def mouseHandler(event, x, y, flags, param):

	global calibration
	global tool_position
	global clicks

	if event == cv.CV_EVENT_LBUTTONDOWN:
		print x,y

		if clicks == 0:
			transx = 270 - (x / 13.)
			transy = 30 - (y / 12.5)
			calibration.reset(transx,transy)
			clicks = clicks + 1

			xrob = uniform(250,280)
			yrob = uniform(25,45)
			command = 'G1 X%d Y%d F10000' % (xrob,yrob)
			p.send_now(command)
			tool_position = []
			tool_position.append(xrob)
			tool_position.append(yrob)

		elif clicks < 11:
			calibration.propagate(x/13.,y/13., tool_position[0], tool_position[1])
			calibration.updateWeights(tool_position[0], tool_position[1])
			print "tool_position", tool_position
			tool_position = [] # reset
			calibration.estimateState()
			print "estimation"
			print calibration.estimation[0], calibration.estimation[1]
			calibration.reSampling()

			xrob = uniform(250,280)
			yrob = uniform(25,45)
			command = 'G1 X%d Y%d F10000' % (xrob,yrob)
			p.send_now(command)
			tool_position = []
			tool_position.append(xrob)
			tool_position.append(yrob)
			clicks += 1
		else:
			robx = x/13.0 + calibration.estimation[2]
			roby = y/12.5 + calibration.estimation[3]
			command = 'G1 X%d Y%d F10000' % ( robx, roby )
			p.send_now(command)


if __name__ == "__main__":

	import printcore
	p=printcore.printcore("/dev/tty.usbserial-A4008eY6",115200)
	#p.loud=True
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

	cv.SetMouseCallback("Undistort", mouseHandler, 0)

	calibration = Condensation(50, 0, 0)

	clicks = 0
	tool_position = [] # different tool positions. right now is static
	cv.SetMouseCallback("Undistort", mouseHandler, 0)

	p.send_now("G1 X270 Y30 F10000")
	tool_position.append(270)
	tool_position.append(30)

	while(1):
		image=cv.QueryFrame(capture)
		t = cv.CloneImage(image);
		cv.Remap( t, image, mapx, mapy )
		cv.Flip(image,image,1)
		cv.ShowImage("Undistort", image)
		c = cv.WaitKey(10)
		if c == 'q':		# enter 'q' key to exit
			break

