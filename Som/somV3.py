from __future__ import division
from random import random,shuffle
from math import exp,log, sqrt
from sys import maxint
import numpy as np
from time import time
import cv
import pickle


class Som:

	def __init__(self, cellsSide, numIts, dimensions, learningRate):

		self.numIts = numIts
		self.cellsSide = cellsSide
		self.learningRate = learningRate

		# create all the nodes
		self.nodes = np.array([ [[ random() for i in range(dimensions) ] for i in range(cellsSide)] for j in range(cellsSide) ])

		# this is the topological 'radius' of the feature map
		self.mapRadius = cellsSide / 2

		# used in the calculation of the neighbourhood width of m_dInfluence
		self.timeConstant = numIts / log(self.mapRadius)

	def FindBestMatchingNode(self, data):
		'''this function presents an input vector to each node in the network
	  		and calculates the Euclidean distance between the vectors for each
  			node. It returns a pointer to the best performer'''

  		#this is an array operation, kind of like matlab
  		position = ((self.nodes-data)**2).sum(axis=2).argmin()
		i = int(position / len(self.nodes))
		j = int(position % len(self.nodes))

  		return (i,j)

	def train(self, training_data):

		learningRate = self.learningRate

		for it in xrange(self.numIts):
			print it
			# shuffle the training data to have a different order each iteration
			np.random.shuffle(training_data)

			for data in training_data:

				# present the vector to each node and determine BMU
				winningNode = self.FindBestMatchingNode(data)

				# calculate the width of the neighbourhood for this timestep
				neighbourhoodRadius = self.mapRadius*exp(-(it+1)/self.timeConstant)
				widthSq = neighbourhoodRadius**2


				left = winningNode[0] - round(neighbourhoodRadius)
				if left < 0: left = 0
				right = winningNode[0] + round(neighbourhoodRadius)
				if right > len(self.nodes): right = len(self.nodes)
				up = winningNode[1] - round(neighbourhoodRadius)
				if up < 0: up = 0
				down = winningNode[1] + round(neighbourhoodRadius)
				if down > len(self.nodes): down = len(self.nodes)

				for i in xrange(int(left), int(right)):
					for j in xrange(int(up), int(down)):

						# calculate the Euclidean distance (sq) to this node from the BMU
						distToNodeSq = (winningNode[0] - i)**2 + (winningNode[1]-j)**2

						if distToNodeSq <= widthSq:

							# calculate by how much its weights are adjusted
							influence = exp( -(distToNodeSq) / (2*widthSq) )
							self.nodes[i,j] += learningRate * influence * (data-self.nodes[i,j])

			learningRate = self.learningRate * exp( -(it+1) / self.numIts)


if __name__ == "__main__":

	sideSize = 50
	iterations = 50
	dimensions = 3
	learningRate = 0.05

	time_start = time()

	som = Som(sideSize, iterations, dimensions, learningRate)

	training_data = [ [1,0,0], [0,1,0], [0,0.5,0.25], [0,0,1], [0,0,0.5], [1,1,0.2], [1,0.4,0.25], [1,0,1]]
	f = open('trackNorm.txt', 'r')
	x = pickle.load(f)
	som.train(np.array(x))

	results = cv.CreateImage( (500, 500), 8, 3)
	sideSquare = 500/sideSize
	for i in xrange(sideSize):
		for j in xrange(sideSize):
			cv.Rectangle(results, (int(i*sideSquare), int(j*sideSquare)), (int(i*sideSquare+sideSquare), int(j*sideSquare+sideSquare)), 
				(som.nodes[i,j,0]*255, 
				som.nodes[i,j,1]*255, 
				som.nodes[i,j,2]*255), 
				cv.CV_FILLED)
	
	cv.NamedWindow('results', cv.CV_WINDOW_AUTOSIZE)
	cv.ShowImage('results', results)
	time_end = time()
	print time_end - time_start
	key = cv.WaitKey()

