from random import random, uniform
from math import sqrt, cos, sin


class Condensation:

	def __init__(self, numParticles, iniX, iniY, maxX, maxY):
		''' iniX iniY maxX and maxY refer to the area where initially and randomly
		we will place the particles'''

		self.numTargets = 0
		self.iniX = iniX
		self.iniY = iniY
		self.maxX = maxX
		self.maxY = maxY
		self.numParticles = numParticles #num particles per target
		self.particles = []
		self.estimation = []

	def propagate(self, propData):

		for col in self.particles:
			for particle in col:
				target = propData[particle.myTarget]
				particle.propagate(target)

	def updateWeights(self, propData):

		for col in self.particles:
			for particle in col:
				particle.updateWeight(propData[particle.myTarget])

			sum_weight = 0.0
			for particle in col:
				sum_weight += particle.weight

			for particle in col:
				particle.normWeight(sum_weight)

	def reSampling(self):

		for t in xrange(self.numTargets):

			temp_particles = []

			cumulative = [0] * (self.numParticles+1)
			
			for i in xrange(self.numParticles):
				cumulative[i+1] = cumulative[i] + self.particles[t][i].weight

			for i in xrange(self.numParticles):
				ranNum = random()
				k = 1
				while ranNum > cumulative[k]: 
					k+=1
				temp_particles.append( self.particles[t][k-1].copy() )

			while len(temp_particles) < self.numParticles:
				randParticle = int( uniform( 0, self.numParticles ) )
				temp_particles.append( self.particles[t][randParticle].copy() )

			self.particles[t] = temp_particles


	def estimateState(self):

		for t in xrange(self.numTargets):

			self.estimation[t] = dict(x=0.0, y=0.0)
			ww = 0.0
			for particle in self.particles[t]:
				self.estimation[t]['x'] += particle.weight * particle.x
				self.estimation[t]['y'] += particle.weight * particle.y


	def addTarget(self):

		self.particles.append([])
		self.estimation.append(dict(x=0.0, y=0.0))

		for i in range(self.numParticles):
			x = uniform(self.iniX, self.maxX) #generate a ran num between iniX and maxX
			y = uniform(self.iniY, self.maxY)
			self.particles[self.numTargets].append( Particle(x,y, self.numTargets) )

		self.numTargets+=1


class Particle:

	def __init__(self, inX, inY, target2follow):
		self.x = inX
		self.y = inY
		self.weight = 0
		self.myTarget = target2follow

	def copy(self):
		newParticle = Particle(self.x, self.y, self.myTarget)
		newParticle.weight = self.weight
		return newParticle

	def propagate(self, propData):

		ranDir = uniform(-0.5, 0.5)
		ranDis = uniform(0, 3)

		self.x += ( (propData['speed'] + propData['acceleration']/2) 
				* cos(propData['direction']+propData['changeDirection']+ranDir) * ranDis )
		self.y += ( (propData['speed'] + propData['acceleration']/2) 
				* sin(propData['direction']+propData['changeDirection']+ranDir) * ranDis )


	def updateWeight(self, propData):
		self.weight = 1 / sqrt( (propData['lastPoint']['x']-self.x)**2 
								+ (propData['lastPoint']['y']-self.y)**2 )

	def normWeight(self, sums):
		self.weight = self.weight / sums
