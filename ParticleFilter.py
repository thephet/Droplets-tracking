from random import random, uniform
from math import sqrt, cos, sin


class Condensation:

	def __init__(self, numParticles, iniX, iniY, maxX, maxY):
		''' iniX iniY maxX and maxY refer to the area where initially and randomly
		we will place the particles'''

		self.numTargets = 0
		self.numParticles = numParticles
		self.particles = []
		self.estimation = []

		for i in range(numParticles):
			x = uniform(iniX, maxX) #generate a ran num between iniX and maxX
			y = uniform(iniY, maxY)
			self.particles.append( Particle(x,y) )


	def propagate(self, propData):

		for particle in self.particles:
			target = particle.myTarget()
			target = propData[target]
			particle.propagate(target)

	def updateWeights(self, propData):

		for particle in self.particles:
			particle.updateWeights(propData)

		sum_weights = [0] * self.numTargets
		for particle in self.particles:
			for j in range(self.numTargets):
				sum_weights[j] += particle.weights[j]

		for particle in self.particles:
			particle.normWeight(sum_weights)

	def reSampling(self):

		temp_particles = []

		for j in range(self.numTargets):
			cumulative = [0] * (self.numParticles+1)
			
			for i in range(self.numParticles):
				cumulative[i+1] = cumulative[i] + self.particles[i].weights[j]

			for i in range(self.numParticles/self.numTargets):
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

		self.estimation = [dict(x=0, y=0) for i in range(self.numTargets)]
		x = [0] * self.numTargets
		y = [0] * self.numTargets
		counter = [0] * self.numTargets

		for particle in self.particles:
			target = particle.myTarget()
			x[target] += particle.weights[target] * particle.x
			y[target] += particle.weights[target] * particle.y
			counter[target] += particle.weights[target]

		for i in range(self.numTargets):
			if counter[i] > 0:
				self.estimation[i]['x'] = x[i] / counter[i]
				self.estimation[i]['y'] = y[i] / counter[i]


	def addTarget(self):
		self.numTargets+=1
		for particle in self.particles:
			particle.weights.append(0)
			particle.targets.append(0)



class Particle:

	def __init__(self, inX, inY):
		self.x = inX
		self.y = inY
		self.weights = []
		self.targets = []

	def copy(self):
		newParticle = Particle(self.x, self.y)
		newParticle.weights = self.weights[:]
		newParticle.targets = self.targets[:]
		return newParticle

	def propagate(self, propData):

		ranDir = uniform(-0.5, 0.5)
		ranDis = uniform(0, 3)

		self.x += ( (propData['speed'] + propData['acceleration']/2) 
				* cos(propData['direction']+propData['changeDirection']+ranDir) * ranDis )
		self.y += ( (propData['speed'] + propData['acceleration']/2) 
				* sin(propData['direction']+propData['changeDirection']+ranDir) * ranDis )


	def updateWeights(self, propData):

		for i in xrange(len(self.weights)):
			pData = propData[i]
			self.weights[i] = 1 / sqrt( (pData['lastPoint']['x']-self.x)**2 
								+ (pData['lastPoint']['y']-self.y)**2 )
			self.targets[i] += self.weights[i]

	def normWeight(self, sums):

		for i in xrange(len(self.weights)):
			self.weights[i] = self.weights[i] / sums[i]

	def myTarget(self):

		maxTarget = 0
		maxVal = self.targets[0]

		for i in xrange(1,len(self.targets)):
			if self.targets[i] > maxVal:
				maxTarget = i
				maxVal = self.targets[i]
		return maxTarget
