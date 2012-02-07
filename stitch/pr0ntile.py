#!/usr/bin/python
'''
pr0ntile: IC die image stitching and tile generation
Copyright 2012 John McMaster <JohnDMcMaster@gmail.com>
Licensed under a 2 clause BSD license, see COPYING for details


This program solves the following issue:

For very large image assemblies it eventually becomes impractical to represent the entire thing as one image
Even if a large stitched image is availible its better to convert it to a number of smaller "tiles" and display
them with Google Maps like software

It takes a considerable amount of work to create very large stitches
This program streamlines this process by instead creating the titles a little at a time
It does this by forming quadrants that are then used to form the final image

Images will be output truncated to the ends
Inputs:
-X tile dimmension (pixels)
-Y tile dimmension (pixels)


Algorithm
-Load project file in using my pypto library
-Parse out total width and the active rectangle
-For each tile generated:
	-Generate a project cropped to the given tile area
	-Run through nona and then enblend to produce a tile
	Note that images may be shared between tiles
	Is it possible to use nona to generate all of the images and then selectively enblend them?
		maybe but its more work, don't do for first pass
	

The workflow is thus:
-Run pr0nstitch to generate control points
-Hugin: ru optimizer
	TODO: can I do this by hand?)  
	It seems this logic might be too engrained into Hugin?
	I'm not sure how to use PTOptimizer or at least it might take a lot of work to interface to it
-Hugin crop and stuff so its reasonable
	TODO: now that I will be messing with this a little more I wonder if I can omit this
-Run this on the resulting optimized project file
	The optimized project should make sure that we keep good position even as we move around
	Note that the above optimization does not require loading the actual images, its more of a traveling salesman type problem

TODO:
If a lower res image was availible it might be nice to match features and scale to it



'''

import sys 
import os.path
from pr0ntools.tile.tile import from_single
from pr0ntools.stitch.wander_stitch import WanderStitch
from pr0ntools.stitch.grid_stitch import GridStitch
from pr0ntools.stitch.fortify_stitch import FortifyStitch
from pr0ntools.execute import Execute

VERSION = '0.1'


def usage():
	print 'pr0ntile <image file names>'
	print 'single file name will expect one gigantic input'
	print 'multiple file names will be stitched together and must overlap'


if __name__ == "__main__":
	if len(sys.argv) > 2:
		files_in = []
		#for i in range(1, len(sys.argv)):
		#	files_in.append(
		files_in += sys.argv[1:len(sys.argv)]
		print 'Processing files %s' % str(files_in)
		from_multi(files_in, max_level, min_level)
	elif len(sys.argv) == 2:
		min_level = 0
		max_level = 3
		'''
		Test file is the carved out metal sample of the 6522
		It is 5672 x 4373 pixels
		I might do a smaller one first
		'''
		#fn = 'xc9536xl_vqg44awn1105__neo50xulwd__semipol_lev_noz_dirty.jpg'
		if len(sys.argv) < 2:
			#fn = '1024x1024.jpg'
			# filename I typically put out from hugin
			fn = 'out.jpg'
		else:
			fn = sys.argv[1]
		from_single(fn, max_level, min_level)
	else:
		usage()
		sys.exit(1)
		
