import cv # opencv
import printcore # this controls the robot
from time import time, sleep, localtime
from math import atan2, sqrt, sin, cos
import pickle
import numpy as np

import RobCamCalibration.TMsolver as tm


def mouseHandler(event, x, y, flags, param):

	global droplets

	if event == cv.CV_EVENT_LBUTTONDOWN:
		frameCopy = cv.CreateImage(cv.GetSize(param), param.depth, param.channels)
		cv.Copy(param, frameCopy)
		fillResult = cv.FloodFill(frameCopy, (x,y), 
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
		newDroplet = { 'morpho1' : cv.CreateStructuringElementEx( int(squareSide), 
									int(squareSide), int(squareSide/2), int(squareSide/2), 
									cv.CV_SHAPE_ELLIPSE),
						'morpho2' : cv.CreateStructuringElementEx( int(squareSide/2), 
									int(squareSide/2), int(squareSide/4), int(squareSide/4), 
									cv.CV_SHAPE_ELLIPSE),
						'avgColor': colorAvg,
						'speed':0, 'acceleration':0, 'direction':0, 'changeDirection':0,
						'lastPoint': { 'x':x, 'y':y },
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

	# only returns the biggest one... because there is some noise in the handling
	# and small bubbles that we want to ignore and I cannot delete them
	# with morpho operations
	biggest_area = 0
	while contour:
		# Approximates rectangles
		bound_rect = cv.BoundingRect(list(contour))
		area = bound_rect[2] * bound_rect[3]
		if (area > biggest_area):
			centers = []
			centers.append( 
				(int(bound_rect[0] + (bound_rect[2] / 2.0)), 
				int(bound_rect[1] + (bound_rect[3] / 2.0)))
				)
			biggest_area = area

		contour = contour.h_next()

	return centers
	

if __name__ == "__main__":

	p = printcore.printcore("/dev/tty.usbserial-A4008eY6",115200)
	#p.loud=True
	sleep(3)
	calibration = tm.TMSolver(p)
	gcode = [i.replace("\n","") for i in open( "/Users/joanmanel/Documents/thesis/gcode/first droplets/water_and_oil.gcode" )]
	p.startprint(gcode)
	sleep(3)

	cv.NamedWindow('video', cv.CV_WINDOW_AUTOSIZE)
	cv.NamedWindow('threshold', cv.CV_WINDOW_AUTOSIZE)
	cv.NamedWindow('path', cv.CV_WINDOW_AUTOSIZE)

	capture = cv.CaptureFromCAM(1) # from webcam
	frame  = cv.QueryFrame(capture) # grab 1 frame to init everything

	newvideo = 'Videos/%d.%d.%d-%d:%d:%d.avi' % (localtime()[2],localtime()[1],localtime()[0],localtime()[3],localtime()[4],localtime()[5])
	video = cv.CreateVideoWriter(newvideo, cv.CV_FOURCC('D','I','V','X'), 30, cv.GetSize(frame), 1)

	newfile = 'Som/data/%d.%d.%d-%d:%d:%d.txt' % (localtime()[2],localtime()[1],localtime()[0],localtime()[3],localtime()[4],localtime()[5])

	# prepare for undistortion
	intrinsic = cv.Load("CamCalibration/Intrinsics.xml")
	distortion = cv.Load("CamCalibration/Distortion.xml")
	mapx = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_32F, 1 );
	mapy = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_32F, 1 );
	cv.InitUndistortMap(intrinsic,distortion,mapx,mapy)
	t = cv.CloneImage(frame)
	cv.Remap( t, frame, mapx, mapy ) # undistort
	cv.Flip(frame, frame, 1) # flip around x because the webcam is like a mirror

	# to store the results from the color seg
	colorThreshed = cv.CreateImage(cv.GetSize(frame), 8, 1)

	#to show the path
	pathImg = cv.CreateImage(cv.GetSize(frame), frame.depth, frame.channels)
	cv.Set(pathImg, cv.ScalarAll(255))

	key, pause = 1,1 # key is keyboard input, pause for playing/pause video
	FPS = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	FPS = 30 # somehow the previous line returns 0 for cams. 30 is the default
	frame_period = 1.0 / FPS

	cv.SetMouseCallback('video', mouseHandler, frame)

	droplets = [] # this will hold all the droplets found
	frames = 0 # to count the number of frames
	track_info = [] # a list to place position, speed, change of direction... of droplets over time

	rebubbling = 0 #when this is 10, it will do the rebubbling condition
	removed = 1 #set to 1 when a droplet inside oil is removed
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
			frame  = cv.QueryFrame(capture) # grab 1 frame to init everything
			if not frame: break
			t = cv.CloneImage(frame)
			cv.Remap( t, frame, mapx, mapy )
			cv.Flip(frame, frame, 1)
			if len(droplets) > 0:
				cv.WriteFrame(video, frame)

		frames += 1
		# we will do something every s if we checked frames == 0
		if frames > FPS: 
			frames = 0

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

				# morpho operations to clean the results
				# cv.Erode( colorThreshedTemp, colorThreshedTemp, current['morpho2'])
				cv.Dilate( colorThreshedTemp, colorThreshedTemp, current['morpho1'])
				cv.MorphologyEx( colorThreshedTemp, colorThreshedTemp, None,
								current['morpho2'], cv.CV_MOP_CLOSE ) 

				cv.Xor(colorThreshed, colorThreshedTemp, colorThreshed)
				cv.MorphologyEx( colorThreshed, colorThreshed, None,
								current['morpho2'], cv.CV_MOP_OPEN )

			cv.ShowImage('threshold', colorThreshed)

			centers = find_connected_components(colorThreshed)
			foundDrops += len(centers)
			del(colorThreshedTemp)

			if foundDrops > 0 and foundDrops == len(droplets):

				# rebubble
				# this just loads the oil and places and the syringe over the dish at height 55
				# which is tip inside the water
				print rebubbling
				if (rebubbling == 9):

					gcode = [i.replace("\n","") for i in open( "/Users/joanmanel/Documents/thesis/gcode/first droplets/rebubble.gcode" )]
					robx = (centers[0][0]/calibration.sx) * cos(calibration.alpha) - (centers[0][1]/calibration.sy) * sin(calibration.alpha) + calibration.tx	
					roby = (centers[0][0]/calibration.sx) * sin(calibration.alpha) + (centers[0][1]/calibration.sy) * cos(calibration.alpha) + calibration.ty
					print "robot goes here:", robx, roby
					command = 'G1 X%f Y%f F10000' % ( robx-0.5, roby )
					insertion = [command, 'G4 P500', 'M43 P2 S30','G4 P300','M43 P2 S45','G4 P300', 'M43 P3 S169','G4 P300','M43 P2 S62', 'G4 P500', 'M43 P3 S180', 'G4 P1000', 'M43 P2 S0', 'G4 P500', 'G1 X183 Y92', 'G4 P500']
					absortion = ['G4 P3000', command, 'G4 P500', 'M43 P3 S180', 'G4 P500', 'M43 P2 S62', 'G4 P1000', 'M43 P3 S168', 'G4 P1000', 'M43 P2 S0', 'G4 P500', 'G1 X183 Y92', 'G4 P500', 'M43 P3 S180']
					if removed == 0:
						p.startprint(absortion)
						sleep(3)
						removed = 1
					else:
						p.startprint(gcode+insertion)
						sleep(3)
						removed = 0
					rebubbling = 0

				for i in xrange(len(droplets)):

					mycenter = 0 # classic search of best one
					nearer = 9999 #just a big number

					for c in xrange(len(centers)):
						dist = abs(np.linalg.norm( np.array(centers[c]) - 
							np.array( [droplets[i]['lastPoint']['x'],droplets[i]['lastPoint']['y']] ) ))
						if dist < nearer:
							mycenter = c
							nearer = dist

					# if the connected components found something we will update the avg color
					# because the droplet probably moved somewhere else with diff light conditions
					# this is the same as done in the mouse handler
					frameCopy = cv.CreateImage(cv.GetSize(frame), frame.depth, frame.channels)
					cv.Copy(frame, frameCopy)
					fillResult = cv.FloodFill( frameCopy, (centers[mycenter][0],centers[mycenter][1]), 
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

					if squareSide < 2:
						continue

					# we capture the average color generated by the fill area
					cv.SetImageROI( frame, (fillResult[2][0], fillResult[2][1],
												squareSide, squareSide) )
					colorAvg = cv.Avg(frame)
					cv.ResetImageROI(frame)

					# calculate the kinematics
					direction = atan2( centers[mycenter][1] - droplets[i]['lastPoint']['y'],
									centers[mycenter][0] - droplets[i]['lastPoint']['x'] )
					distance = sqrt( (centers[mycenter][0] - droplets[i]['lastPoint']['x'])**2 +
								(centers[mycenter][1] - droplets[i]['lastPoint']['y'])**2 )
					speed = distance / 1

					if speed < 3:
						rebubbling += 1
					else:
						rebubbling = 0

					cv.Line( pathImg, (droplets[i]['lastPoint']['x'], droplets[i]['lastPoint']['y']), 
						(centers[mycenter][0],centers[mycenter][1]), droplets[i]['avgColor'] );

					droplets[i]['acceleration'] = speed - droplets[i]['speed']
					droplets[i]['changeDirection'] = direction - droplets[i]['direction']
					droplets[i]['speed'] = speed
					droplets[i]['direction'] = direction
					droplets[i]['lastPoint']['x'] = centers[mycenter][0]
					droplets[i]['lastPoint']['y'] = centers[mycenter][1]

					track_info[i].append([ droplets[i]['lastPoint']['x'],droplets[i]['lastPoint']['y'],speed, droplets[i]['changeDirection']])
					print speed, droplets[i]['changeDirection']

					# update the morpho elements and the avg color
					droplets[i]['morpho1'] = cv.CreateStructuringElementEx( squareSide, 
												squareSide, squareSide/2, squareSide/2, 
												cv.CV_SHAPE_ELLIPSE)
					droplets[i]['morpho2'] = cv.CreateStructuringElementEx( int(squareSide/2), 
												int(squareSide/2), int(squareSide/4), int(squareSide/4), 
												cv.CV_SHAPE_ELLIPSE)
					droplets[i]['avgColor'] = colorAvg

		cv.ShowImage('video', frame)
		cv.ShowImage('path',pathImg)

		time_end = time()
		cycle_time = time_end - time_start
		delay = frame_period - cycle_time

		if delay < 0: delay = 0
		if delay > frame_period: delay = frame_period

		key = cv.WaitKey( int(delay*1000)+1 )

	newfile = 'Som/data/%d_%d_%d_%d_%d_%d.txt' % (localtime()[0],localtime()[1],localtime()[2],localtime()[3],localtime()[4],localtime()[5])
	f = open(newfile, 'w')
	pickle.dump(track_info[0] ,f)
	f.close()

	del(capture)
	del(frame)
	del(colorThreshed)
	del(pathImg)
	del(video)
	cv.DestroyWindow('video')
	cv.DestroyWindow('path')
	cv.DestroyWindow('threshold')
