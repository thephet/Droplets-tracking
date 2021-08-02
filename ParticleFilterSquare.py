from random import random, uniform
from math import sqrt, cos, sin
import numpy as np


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

    def propagate(self, p):

	    for col in self.particles:
		    for particle in col:
                        particle.propagate(p)

    def updateWeights(self, laser):

	    for col in self.particles:
		    for particle in col:
			    particle.updateWeight(laser)

		    sum_weight = 0.0
		    for particle in col:
			    sum_weight += particle.weight

		    for particle in col:
			    particle.normWeight(sum_weight)

    def reSampling(self):

	    for t in range(self.numTargets):

		    temp_particles = []

		    cumulative = [0] * (self.numParticles+1)
		    
		    for i in range(self.numParticles):
			    cumulative[i+1] = cumulative[i] + self.particles[t][i].weight

		    for i in range(self.numParticles):
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

	    for t in range(self.numTargets):

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
        self.weight = 0.1
        self.myTarget = target2follow

    def copy(self):
        newParticle = Particle(self.x, self.y, self.myTarget)
        newParticle.weight = self.weight
        return newParticle

    def propagate(self, p):

        p = np.array(p)
        vector = p

        self.x += vector[1] * uniform(0.9, 1.1)
        self.y += vector[0] * uniform(0.9, 1.1)

    def updateWeight(self, carlaser):
        part_laser = min(self.x, self.y, 600-self.x, 400-self.y)
        self.weight = 1 / ( abs(carlaser - part_laser) + 1)

    def normWeight(self, sums):
        self.weight = self.weight / sums
