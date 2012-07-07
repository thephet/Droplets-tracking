# Based on the C++ implementation of ai-junkie
# it is almost a direct translation from C++ to Python

from __future__ import division
from random import random,shuffle
from math import exp,log, sqrt
from sys import maxint
from time import time
import cv
import pickle
import numpy as np

class Node:

	def __init__(self, x, y, numWeights):
		
		self.x = x
		self.y = y
		self.weights = [ random() for i in range(numWeights) ]

	def calculateDistance(self, data):

		distance = 0

		for i in xrange(len(self.weights)):
			distance += (data[i] - self.weights[i])**2

		return distance

	def adjustWeights(self, data, learningRate, influence):

		for w in xrange(len(data)):
			self.weights[w] += learningRate * influence * (data[w] - self.weights[w])

class Som:

	def __init__(self, cellsSide, numIts, dimensions, learningRate):

		self.numIts = numIts
		self.cellsSide = cellsSide
		self.learningRate = learningRate

		# create all the nodes
		self.nodes = [ Node(i, j, dimensions) for i in range(cellsSide) for j in range(cellsSide) ]

		# this is the topological 'radius' of the feature map
		self.mapRadius = cellsSide / 2

		# used in the calculation of the neighbourhood width of m_dInfluence
		self.timeConstant = numIts / log(self.mapRadius)

	def FindBestMatchingNode(self, data):
		'''this function presents an input vector to each node in the network
	  		and calculates the Euclidean distance between the vectors for each
  			node. It returns a pointer to the best performer'''

  		lowestDistance = maxint

		for node in self.nodes:
			
			dist = node.calculateDistance(data)

			if dist < lowestDistance:
				lowestDistance = dist
				winner = node

		return winner

	def train(self, td):

		L = [ [ abs(item) for item in row] for row in td ] #abs the array
		self.dimMaxs = [ max(row[column] for row in L) for column in xrange(len(L[0])) ] #find max for each col
		training_data = np.array([ [row[i] / self.dimMaxs[i] for i in xrange(len(row))] for row in L]) #normalize

		learningRate = self.learningRate

		for it in xrange(self.numIts):
			print it
			# shuffle the training data to have a different order each iteration
			shuffle(training_data)

			for data in training_data:

				# present the vector to each node and determine BMU
				winningNode = self.FindBestMatchingNode(data)

				# calculate the width of the neighbourhood for this timestep
				neighbourhoodRadius = self.mapRadius*exp(-(it+1)/self.timeConstant)

				# Now to adjust the weight vector of the BMU and its neighbours		
				# For each node calculate the m_dInfluence (Theta from equation 6 in
				# the tutorial. If it is greater than zero adjust the node's weights
				# accordingly

				for node in self.nodes:

					# calculate the Euclidean distance (sq) to this node from the BMU
					distToNodeSq = (winningNode.x - node.x)**2 + (winningNode.y - node.y)**2
					#print winningNode.x, node.x, winningNode.y, node.y, distToNodeSq, neighbourhoodRadius**2

					widthSq = neighbourhoodRadius**2
					#print distToNodeSq, widthSq
					# if within the neighbourhood adjust its weights
					if distToNodeSq <= widthSq:

						# calculate by how much its weights are adjusted
						influence = exp( -(distToNodeSq) / (2*widthSq) )
						node.adjustWeights(data, learningRate, influence)

			learningRate = self.learningRate * exp( -(it+1) / self.numIts)


if __name__ == "__main__":

	sideSize = 200
	iterations = 5
	dimensions = 2
	learningRate = 0.05

	time_start = time()

	som = Som(sideSize, iterations, dimensions, learningRate)

	#training_data = [ [1,0,0], [0,1,0], [0,0.5,0.25], [0,0,1], [0,0,0.5], [1,1,0.2], [1,0.4,0.25], [1,0,1]]
	f = open('data/2012_5_3_12_55_39.txt', 'r') #droplets.mov blue droplet
	x = pickle.load(f)
	f = open('data/2012_5_3_12_33_10.txt', 'r') #droplets.mov red droplet
	y = pickle.load(f)
	print len(x+y)
	som.train((x+y))

	results = cv.CreateImage( (500, 500), 8, 3)
	sideSquare = 500/sideSize
	for i in xrange(sideSize):
		for j in xrange(sideSize):
			cv.Rectangle(results, (int(i*sideSquare), int(j*sideSquare)), (int(i*sideSquare+sideSquare), int(j*sideSquare+sideSquare)), 
				(som.nodes[i*sideSize+j].weights[0]*255, 
				som.nodes[i*sideSize+j].weights[1]*255, 
				0), 
				cv.CV_FILLED)
	
	cv.NamedWindow('results', cv.CV_WINDOW_AUTOSIZE)
	cv.ShowImage('results', results)
	time_end = time()
	print time_end - time_start
	key = cv.WaitKey()


