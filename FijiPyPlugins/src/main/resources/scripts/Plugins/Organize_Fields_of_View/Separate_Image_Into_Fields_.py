#@ File(label='Where is the folder containing the separate channels of the image you would like to divide into fields of view?',style='directory') input_dir

'''
Separate Image Into Fields

This script can be used to divide up a source image into fields of view
of a particular size.

INPUTS

	- input_dir (java.io.File): Directory containing the separate
								channels of the image the user wanted to
								separate into fields of view.

	The script will also present three additional UIs to the user. In the
	first UI, the user will specify which files represent the separate
	channels of the image they would like to divide into fields of view.
	In the second UI, the user will specify what marker (e.g. DAPI,
	NeuN) was imaged in each channel. The last UI will ask the user to
	specify the field of view size.

OUTPUTS

	The script will automatically divide up the separate channels of the
	image into fields of view. These fields of view will be normalized
	by first using Fiji's automated brightness/contrast adjustment,
	followed by a histogram normalization. All of these fields of view
	from each channel will be saved under separate folders added under
	the input_dir in a folder called FieldsOfView. The ROIs
	corresponding to the location of these fields of view on the source
	image will be saved under a folder called ROIs. The size of the field
	of view will be specified by the user, as well as how much the fields
	should overlap into neighboring fields to help visualize cells along
	the boarder of the field. To get the true boundary of these fields that
	doesn't overlap into neighboring fields, an ROI will be saved in a
	folder called FieldsOfView.

AR Oct 2021
AR Dec 2021 Determine calibration of image to ask user about field of
			view size
AR Jan 2022 Account for rotated tile scans
AR Feb 2022 Save locations of the fields to a csv file
AR Mar 2022 Change files from reporting field size in pixels to microns
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so we can ask the user to specify the folder
# containing the images they would like to separate into unique fields
# of view
from java.io import File

# Convert the input_dir java.io.File object to a string so we know the
# path to the folder containing the images to be processed
inputDir = input_dir.getAbsolutePath()

del input_dir

# Import tools that will allow us to work easily with files
from ImageTools import ImageFiles

# Import regular expressions so we can parse file paths
import re

# Import our user interface and data files libraries
import UIs, DataFiles

# Import generic dialog so we can make quick and dirty UI's
from ij.gui import GenericDialog

# Import os so we can extract the basename of a file and make new
# directories and join path elements
import os

# Import ImagePlus so we can read image files and IJ so we can run
# macros commands
from ij import ImagePlus, IJ
ImagePlus()

# Import our ROITools library
import ROITools

# Import our ImageProcessing library
from ImageTools import ImageProcessing

########################################################################
## IDENTIFY WHICH IMAGE FILES SHOULD BE SEPARATED INTO FIELDS OF VIEW ##
########################################################################

# Search the directory specified by the user to generate a list of all
# files
allFilesInDir = ImageFiles.findImgsInDir(inputDir)

# Ask the user to specify which image files they would like to separate
# into unique fields of view
imgs2separate = UIs.checkBoxUI('Check off all files containing the separate channels imaged over the same area that you would like to separate into fields of view.',
							  allFilesInDir)

del allFilesInDir

########################################################################
###### IDENTIFY WHICH MARKER (E.G. DAPI) WAS IMAGED IN EACH IMAGE ######
########################################################################

markersImaged = UIs.textFieldsUI('Specify the marker (e.g. DAPI, NeuN) imaged in each file.',
								 [os.path.basename(imgPath) for imgPath in imgs2separate],
								 ['DAPI'] * len(imgs2separate))

del imgPath

########################################################################
###################### GENERATE FIELD OF VIEW ROIS #####################
########################################################################

# Open the first image in our list of images we want to separate into
# fields of view
frst_img = ImagePlus(imgs2separate[0])

# Store the dimensions of this first image
frst_img_dims = frst_img.getDimensions()

# Store the image calibration for this first image. This will contain
# information about the pixel to physical unit conversion.
imgCal = frst_img.getCalibration()

# Get the physical length units stored in this image
lengthUnits = imgCal.getUnit()

# Check to see if the micron symbol was used in the length units
if u'\xb5' in lengthUnits:

	# Convert the micron symbol to a u
	lengthUnits = lengthUnits.replace(u'\xb5','u')

# Ask the user to specify the size of the field of view and amount of
# overlap in neighboring fields of view
[field_size_physical,field_overlap_physical] = UIs.textFieldsUI('Specify your true field of view size and the amount you want to see overlaping into neighboring fields.',
											  					['True Field of View Size in {}:'.format(lengthUnits),
											   					 'Overlap into Neighboring Fields in {}:'.format(lengthUnits)],
											  			 		['60','15'])

# Convert field size and field overlap from physical units to pixels
field_size = int(round(imgCal.getRawX(float(field_size_physical))))
field_overlap = int(round(imgCal.getRawX(float(field_overlap_physical))))
del imgCal

# If the image was previously rotated, there will be a text file storing
# the angle of rotation. Find this text file
rotAngleTextFilePath = ImageFiles.findImgsInDir(inputDir,'txt',
											    'RotationInDegrees_')

# Generate a regular expression to get the name of the image we are
# separating into multiple fields of view
regex = re.compile('.*RotationInDegrees_(?P<Image_Name>.*)\.txt')

# Search the text file path for this regular expression
matches = regex.match(str(rotAngleTextFilePath))

# Store the name of the image we are analyzing
imgFileName = matches.groupdict()['Image_Name']

# If the text file wasn't found, the output of the previous command will
# be an empty list
if len(rotAngleTextFilePath) == 0:

	# Store a variable so we know the image wasn't rotated
	rotation = 0

# If we found the text file...
else:

	# Open the text file
	with open(rotAngleTextFilePath,'r+') as rotAngleTextFile:

		# Read the angle saved in the text file
		rotation = float(rotAngleTextFile.read())

		rotAngleTextFile.close()
del rotAngleTextFilePath, rotAngleTextFile

# Separate the image into a grid-like configuration of fields of view
fovGrid = ROITools.gridOfFields(frst_img,field_size,field_overlap,
								rotation)
del field_overlap, rotation

# Create a dictionary that will store the names of all of these fields
# of view as well as their x,y coordinates in physical units
fovNamesLocs = ROITools.getLabelsAndLocations(fovGrid.ROIs,frst_img,
											  False)

# From all of the names of the fields of view, extract just the number,
# which will come after 'Field-' string (see gridOfFields class
# definition)
fovNamesLocs['Field_Number'] = [int(fieldName[6:]) for fieldName in fovNamesLocs['Cell_Type']]
del fovNamesLocs['Cell_Type']

########################################################################
################## SEPARATE IMAGES INTO FIELDS OF VIEW #################
########################################################################

# Define a function that will crop, normalize and save each field of
# view
def crop_norm_save_fov(img2separate,fieldOfViewROI,outDir):
	'''
	Crops, normalizes and save each field of view separated from the larger
	source image

	crop_norm_save_fov(img2separate,fieldOfViewROI,outDir)

		- img2separate (Fiji ImagePlus): The image that you are separating
										 into separate fields of view

		- fieldOfViewROI (Fiji ROI): The ROI specifying the field of view you
									 want to crop from img2separate

		- outDir (String): Path to where you would like to save the final,
						   normalized field of view

	AR Oct 2021
	AR Feb 2022 Make sure images close so they don't take up memory
	'''

	# Crop the field of view from the larger image
	field = ROITools.getImgInROI(img2separate,fieldOfViewROI)

	# Normalize this field of view
	normalizedField = ImageProcessing.normalizeImg(field)

	# Clear the field of view from memory
	field.close()

	# Save this normalized field of view
	IJ.save(normalizedField,os.path.join(outDir,normalizedField.getTitle()))

	# Clear the normalized field of view from memory
	normalizedField.close()

# Define a wrapper function that will crop, normalize and save each
# field of view in a given image to be separated
def breakupIntoFields(img2separate,markerInImg):
	'''
	This function will crop, normalize and save each field of view in a
	given image that needs to be separated.

	breakupIntoFields(img2separate,fieldOfViewROIs,markerInImg)

		- img2separate (Fiji ImagePlus): The image that you are separating
										 into separate fields of view

		- fieldOfViewROIs (List of Fiji ROI): The ROI specifying the field of
											  view you want to crop from
											  img2separate

		- markerInImg (String): Marker (e.g. 'DAPI') imaged in img2separate

	AR Oct 2021
	'''

	# Check to see if the dimensions of this image are equivalent to the
	# dimensions of the first image
	if img2separate.getDimensions() != frst_img_dims:

		raise ValueError('The dimensions of your images are not equivalent. This script is intended to be across multiple channels from the same area imaged.')

	# Store the path to the directory where the fields of view from this
	# channel will be stored
	outDir = os.path.join(inputDir,'FieldsOfView','{}{}Fields_{}{}Overlap.zip'.format(field_size_physical,lengthUnits,field_overlap_physical,lengthUnits),markerInImg)

	# Create this output directory
	ImageFiles.makedir(outDir)

	# Crop, normalize and save all fields of view from this image
	[crop_norm_save_fov(img2separate,fieldOfViewROI,outDir) for fieldOfViewROI in fovGrid.ROIs]

# Breakup the first image into separate fields of view
breakupIntoFields(frst_img,markersImaged[0])

# Delete the first image from memory
frst_img.close()
del frst_img

# Loop across all images whose fields of view need to be separated as
# well as their respective markers
for imgPath, marker in zip(imgs2separate[1:],markersImaged[1:]):

	# Read the image file into an ImagePlus object
	img = ImagePlus(imgPath)

	# Breakup the image into separate fields of view
	breakupIntoFields(img,marker)

	# Clear the current image from memory
	img.close()
	del img

del imgs2separate, markersImaged, frst_img_dims, imgPath, marker

########################################################################
######################## SAVE FIELD OF VIEW ROIS #######################
########################################################################

# Write a file path to where we want to save our set of Field of View
# ROIs
fieldROIsPath = os.path.join(inputDir,'ROIs','{}{}Fields_{}{}Overlap.zip'.format(field_size_physical,lengthUnits,field_overlap_physical,lengthUnits))

# Save the field of view ROIs to this file path
ROITools.saveROIs(fovGrid.ROIs,fieldROIsPath)

del fieldROIsPath

# Write a file path to where we want to save a csv file with all of the
# field of view numbers and x,y coordinates in physical units
fieldCoordsPath = os.path.join(inputDir,'FieldsOfView','{}{}Fields_{}{}Overlap.zip'.format(field_size_physical,lengthUnits,field_overlap_physical,lengthUnits),'{}{}FieldLocations_{}.csv'.format(field_size_physical,lengthUnits,imgFileName))

# Save the field x and y coordinates to a csv file
DataFiles.dict2csv(fovNamesLocs,fieldCoordsPath)

del fovNamesLocs, fieldCoordsPath

# Write a file path to where we want to save our Field boundary ROI
fieldBoundaryROIPath = os.path.join(inputDir,'FieldsOfView','{}{}Fields_{}{}Overlap.zip'.format(field_size_physical,lengthUnits,field_overlap_physical,lengthUnits),'{}{}FieldBoundary.zip'.format(field_size_physical,lengthUnits))

del inputDir, field_size

# Save the field of view boundary ROI to this file path
ROITools.saveROIs(fovGrid.fieldBoundary,fieldBoundaryROIPath)

del fovGrid, fieldBoundaryROIPath
