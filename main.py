import cv
from time import time
from math import atan2, sqrt
import pickle

import ParticleFilter as pf


def mouseHandler(event, x, y, flags, param):

	global droplets

	if event == cv.CV_EVENT_LBUTTONDOWN:
		frameCopy = cv.CreateImage(cv.GetSize(param), param.depth, param.channels)
		cv.Copy(param, frameCopy)
		fillResult = cv.FloodFill( frameCopy, (x,y), 
								cv.RGB(250,0,0), 
								cv.ScalarAll(3), cv.ScalarAll(3), 8 )
		del(frameCopy)

		# generate 2 struct element for morpho operations
		# the size will be the min, to be safe
		if fillResult[2][2] > fillResult[2][3]: # fillResult.rect.width > fillResult.rect.height
			squareSide = fillResult[2][3]
		else:
			squareSide = fillResult[2][2]
		# the masks need to be odd
		if squareSide % 2 == 0: squareSide+=1

		# we capture the average color generated by the fill area
		cv.SetImageROI( param, (fillResult[2][0], fillResult[2][1],
									squareSide, squareSide) )
		colorAvg = cv.Avg(param)
		cv.ResetImageROI(param)

		# generate the new found droplet
		newDroplet = { 'morpho1' : cv.CreateStructuringElementEx( squareSide, 
									squareSide, squareSide/2, squareSide/2, 
									cv.CV_SHAPE_ELLIPSE),
						'morpho2' : cv.CreateStructuringElementEx( squareSide/2, 
									squareSide/2, squareSide/4, squareSide/4, 
									cv.CV_SHAPE_ELLIPSE),
						'avgColor': colorAvg,
						'speed':0, 'acceleration':0, 'direction':0, 'changeDirection':0,
						'lastPoint': { 'x':x, 'y':y }
					}
		droplets.append(newDroplet)

		track_info.append([]) #add another list here to add the info about the droplet's movement


def find_connected_components(img):
	"""Find the connected components in img being a binary image.
	it approximates by rectangles and returns its centers
	"""

	storage = cv.CreateMemStorage(0)
	contour = cv.FindContours(img, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
	centers = []

	while contour:
		# Approximates rectangles
		bound_rect = cv.BoundingRect(list(contour))
		centers.append( (bound_rect[0] + bound_rect[2] / 2, 
						bound_rect[1] + bound_rect[3] / 2) )
		contour = contour.h_next()

	return centers

# normalize the list and abs
def prepare_track_data(L):
	L = [ [ abs(item) for item in row] for row in L ] # abs the list
	maxs = [ max(row[column] for row in L) for column in xrange(len(L[0])) ] # max for each column
	return [ [row[i] / maxs[i]*255 for i in xrange(len(row))] for row in L] # normalize each list
	

if __name__ == "__main__":

	cv.NamedWindow('video', cv.CV_WINDOW_AUTOSIZE)
	cv.NamedWindow('threshold', cv.CV_WINDOW_AUTOSIZE)
	cv.NamedWindow('particles', cv.CV_WINDOW_AUTOSIZE)

	capture = cv.CreateFileCapture('droplets.mov')
	frame = cv.QueryFrame(capture) # grab 1 frame to init everything

	# to store the results from the color seg
	colorThreshed = cv.CreateImage(cv.GetSize(frame), 8, 1)

	# to show the particles
	particlesImg = cv.CreateImage(cv.GetSize(frame), frame.depth, frame.channels)

	key, pause = 1,1 # key is keyboard input, pause for playing/pause video
	frame_period = 1/cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	FPS = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)

	cv.SetMouseCallback('video', mouseHandler, frame)

	droplets = [] # this will hold all the droplets found
	frames = 0 # to count the number of frames
	track_info = [] # a list to place position, speed, change of direction... of droplets over time

	num_particles = 100
	condensation = pf.Condensation(num_particles, 200, 0, frame.width, frame.height)

	while(1):

		time_start = time()

		if key == 97: # 97 is 'a'
			if pause == 1:
				pause = 0
			else:
				pause = 1
		elif key == 27:
			break
			
		if pause == 1:
			frame = cv.QueryFrame(capture)
			if not frame: break
			cv.Copy(frame, particlesImg)

		frames += 1
		# we will do something every s if we checked frames == 0
		if frames > FPS: 
			frames = 0

		# we need to check that the number of targets being followed is known by the p filter
		while condensation.numTargets < len(droplets):
			condensation.addTarget()

		foundDrops = 0
		if frames == 0 and pause == 1 and len(droplets) > 0:
			
			# blackout results from thresholding to fill in the next lines
			cv.SetZero(colorThreshed)

			for current in droplets:
				# color segmentation
				minRange = cv.Scalar( current['avgColor'][0]-10, current['avgColor'][1]-10, 
									current['avgColor'][2]-10 )
				maxRange = cv.Scalar( current['avgColor'][0]+10, current['avgColor'][1]+10, 
									current['avgColor'][2]+10 )
				colorThreshedTemp = cv.CreateImage( cv.GetSize(frame),8,1 )
				cv.InRangeS(frame, minRange, maxRange, colorThreshedTemp)

				#morpho operations to clean the results
				cv.Dilate( colorThreshedTemp, colorThreshedTemp, current['morpho1'])
				cv.Erode( colorThreshedTemp, colorThreshedTemp, current['morpho2'])
				cv.MorphologyEx( colorThreshedTemp, colorThreshedTemp, None,
								current['morpho1'], cv.CV_MOP_OPEN ) 

				cv.Xor(colorThreshed, colorThreshedTemp, colorThreshed)
				cv.MorphologyEx( colorThreshed, colorThreshed, None,
								current['morpho1'], cv.CV_MOP_OPEN )

			cv.ShowImage('threshold', colorThreshed)

			centers = find_connected_components(colorThreshed)
			foundDrops += len(centers)
			del(colorThreshedTemp)

			if len(centers) > 0 and foundDrops == len(droplets):

				for i in range(len(centers)):
					direction = atan2( centers[i][1] - droplets[i]['lastPoint']['y'],
									centers[i][0] - droplets[i]['lastPoint']['x'] )
					distance = sqrt( (centers[i][0] - droplets[i]['lastPoint']['x'])**2 +
								(centers[i][1] - droplets[i]['lastPoint']['y'])**2 )
					speed = distance / 1

					droplets[i]['acceleration'] = speed - droplets[i]['speed']
					droplets[i]['changeDirection'] = direction - droplets[i]['direction']
					droplets[i]['speed'] = speed
					droplets[i]['direction'] = direction
					droplets[i]['lastPoint']['x'] = centers[i][0]
					droplets[i]['lastPoint']['y'] = centers[i][1]

					track_info[i].append([ speed, droplets[i]['changeDirection'], 1 ])

					# if the connected components found something we will update the avg color
					# because the droplet probably moved somewhere else with diff light conditions
					# this is the same as done in the mouse handler
					frameCopy = cv.CreateImage(cv.GetSize(frame), frame.depth, frame.channels)
					cv.Copy(frame, frameCopy)
					fillResult = cv.FloodFill( frameCopy, (centers[0][0],centers[0][1]), 
								cv.RGB(250,0,0), cv.ScalarAll(3), cv.ScalarAll(3), 8 )
					del(frameCopy)

					# generate 2 struct element for morpho operations
					# the size will be the min, to be safe
					if fillResult[2][2] > fillResult[2][3]: # fillResult.rect.width > fillResult.rect.height
						squareSide = fillResult[2][3]
					else:
						squareSide = fillResult[2][2]
					# the masks need to be odd
					if squareSide % 2 == 0: squareSide+=1

					# we capture the average color generated by the fill area
					cv.SetImageROI( frame, (fillResult[2][0], fillResult[2][1],
												squareSide, squareSide) )
					colorAvg = cv.Avg(frame)
					cv.ResetImageROI(frame)

					# update the morpho elements and the avg color
					current['morpho1'] = cv.CreateStructuringElementEx( squareSide, 
												squareSide, squareSide/2, squareSide/2, 
												cv.CV_SHAPE_ELLIPSE)
					current['morpho2'] = cv.CreateStructuringElementEx( squareSide/2, 
												squareSide/2, squareSide/4, squareSide/4, 
												cv.CV_SHAPE_ELLIPSE)
					current['avgColor'] = colorAvg

		
		cv.ShowImage('video', frame)


		# if foundDrops == len(droplets) and len(droplets) > 0:
		# 	condensation.propagate(droplets)
		# 	condensation.updateWeights(droplets)
		# 	condensation.reSampling()
		# 	condensation.estimateState()

		# for particle in condensation.particles:
		# 	cv.Circle(particlesImg, (int(particle.x), int(particle.y)), 2, 
		# 							(0,200,200), cv.CV_FILLED)

		# for est in condensation.estimation:
		# 	cv.Circle(particlesImg, (int(est['x']), int(est['y'])), 5, cv.Scalar(0,0,255), cv.CV_FILLED)

		# cv.ShowImage('particles', particlesImg)

		time_end = time()
		cycle_time = time_end - time_start
		delay = frame_period - cycle_time

		if delay < 0: delay = 0
		if delay > frame_period: delay = frame_period

		key = cv.WaitKey( int(delay*1000)+1 )

	L = prepare_track_data(track_info[0])
	f = open('trackblue.txt', 'w')
	pickle.dump(L ,f)

	del(capture)
	del(frame)
	del(colorThreshed)
	del(particlesImg)
	cv.DestroyWindow('video')
	cv.DestroyWindow('particles')
	cv.DestroyWindow('threshold')
