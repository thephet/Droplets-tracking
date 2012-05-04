# THis code is a re-implementation of somBasic.py using numpy.
# It is much faster, like 2x or 4x depending of vector sizes.
# I'd recommend reading first somBasic.py

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

	def save(self, filename):
		''' this function only saves self.nodes, which is the big structure. 
		All the other class attributes aren't saved '''
		toSave = {'numIts':self.numIts, 'cellsSide':self.cellsSide, 'learningRate':self.learningRate, 'nodes':self.nodes, 'dimMaxs':self.dimMaxs}
		f = open(filename, 'wb')
		pickle.dump(toSave, f)

	def FindBestMatchingNode(self, data):
		'''this function presents an input vector to each node in the network
	  		and calculates the Euclidean distance between the vectors for each
  			node. It returns a pointer to the best performer'''

  		#this is an array operation, kind of like matlab
  		position = ((self.nodes-data)**2).sum(axis=2).argmin()
		i = int(position / len(self.nodes))
		j = int(position % len(self.nodes))

  		return (i,j)

	def train(self, td):

		# the training data needs to be normalized
		L = [ [ abs(item) for item in row] for row in td ] #abs the array
		self.dimMaxs = [ max(row[column] for row in L) for column in xrange(len(L[0])) ] #find max for each col
		training_data = np.array([ [row[i] / self.dimMaxs[i] for i in xrange(len(row))] for row in L]) #normalize
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

				#check for the borders to avoid negative indexs.
				left = winningNode[0] - round(neighbourhoodRadius)
				if left < 0: left = 0
				right = winningNode[0] + round(neighbourhoodRadius)
				if right > len(self.nodes): right = len(self.nodes)
				up = winningNode[1] - round(neighbourhoodRadius)
				if up < 0: up = 0
				down = winningNode[1] + round(neighbourhoodRadius)
				if down > len(self.nodes): down = len(self.nodes)

				# select a sub array based in just calculated borders
				subnodes = self.nodes[left:right, up:down]
				wini = winningNode[0] - left
				winj = winningNode[1] - up

				# store in a array the weighted distance from every position to the center
				distToNodeSq = np.array([[ [learningRate*exp(-((wini - i)**2 + (winj-j)**2)/(2*widthSq))] 
					for i in xrange(int(down-up))] 
					for j in xrange(int(right-left))])
				#update every node based on the weithed distance array, numpy operation kind of matlab
				subnodes += distToNodeSq*(data-subnodes)

			learningRate = self.learningRate * exp( -(it+1) / self.numIts)

def load(filename):
	
	f = open(filename, 'rb')
	toLoad = pickle.load(f)

	newSom = Som( toLoad['cellsSide'], toLoad['numIts'], 0, toLoad['learningRate'])
	newSom.nodes = toLoad['nodes']
	newSom.dimMaxs = toLoad['dimMaxs']

	return newSom


if __name__ == "__main__":

	sideSize = 10
	iterations = 30
	dimensions = 2
	learningRate = 0.05

	time_start = time()

	testsom = Som(sideSize, iterations, dimensions, learningRate)

	# training_data = [ [1,0,0], [0,1,0], [0,0.5,0.25], [0,0,1], [0,0,0.5], [1,1,0.2], [1,0.4,0.25], [1,0,1]]
	# som.train(np.array( training_data ))
	#f = open('data/2012_5_3_12_55_39.txt', 'r') #droplets.mov blue droplet
	#x = pickle.load(f)
	#f = open('data/2012_5_3_12_33_10.txt', 'r') #droplets.mov red droplet
	#y = pickle.load(f)
	f = open('data/2012_5_3_19_5_37.txt','r')
	x = pickle.load(f)
	testsom.train(np.array(x))
	testsom.save("data/som.dat")

	results = cv.CreateImage( (500, 500), 8, 3)
	sideSquare = 500/sideSize

	for i in xrange(sideSize):
		for j in xrange(sideSize):
			cv.Rectangle(results, (int(i*sideSquare), int(j*sideSquare)), 
				(int(i*sideSquare+sideSquare), int(j*sideSquare+sideSquare)), 
				(testsom.nodes[i,j,0]*255, testsom.nodes[i,j,1]*255, 0), 
				cv.CV_FILLED)

	cv.NamedWindow('results', cv.CV_WINDOW_AUTOSIZE)
	cv.ShowImage('results', results)
	time_end = time()
	print time_end - time_start
	key = cv.WaitKey()

