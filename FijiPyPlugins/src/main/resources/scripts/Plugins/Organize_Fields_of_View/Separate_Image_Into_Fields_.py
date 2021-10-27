#@ File(label='Where is the folder containing the separate channels of the image you would like to divide into fields of view?',style='directory') input_dir
#@ Short(label='Field of view size in pixels (we recommend 52.5x52.5 micron fields for human cortical regions):',value=581) field_size

'''
Separate Image Into Fields

This script can be used to divide up a source image into fields of view
of a particular size.

INPUTS

	- input_dir (java.io.File): Directory containing the separate
								channels of the image the user wanted to
								separate into fields of view.

	- field_size (Int): Size of the fields you would like, provided in
						pixels. Default 581 works for images with
						 90.2 nm pixels.

	The script will also present two additional UIs to the user. In the
	first UI, the user will specify which files represent the separate
	channels of the image they would like to divide into fields of view.
	In the second UI, the user will specify what marker (e.g. DAPI,
	NeuN) was imaged in each channel.

OUTPUTS

	The script will automatically divide up the separate channels of the
	image into fields of view. These fields of view will be normalized
	by first using Fiji's automated brightness/contrast adjustment,
	followed by a histogram normalization. All of these fields of view
	from each channel will be saved under separate folders added under
	the input_dir in a folder called FieldsOfView. The ROIs
	corresponding to the location of these fields of view on the source
	image will be saved under a folder called ROIs. These fields of view
	will be twice the size specified by the input field_size because
	extra space will be added overlapping 50% into all 4 neighboring
	fields. To get the true boundary of these fields that doesn't
	overlap into neighboring fields, an ROI will be saved in a folder
	called FieldsOfView.

AR Oct 2021
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

# Import generic dialog so we can make quick and dirty UI's
from ij.gui import GenericDialog

# Import os so we can extract the basename of a file and make new
# directories and join path elements
import os

# Import ImagePlus so we can read image files and IJ so we can run
# macros commands
from ij import ImagePlus, IJ

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

# Create a user interface that will ask the user to specify which image
# files they would like to separate into unique fields of view
whichFilesUI = GenericDialog('Check off all files containing the separate channels imaged over the same area that you would like to separate into fields of view.')

# Create checkboxes so that the user can indicate which files they want
# to separate into unique fields of view
whichFilesUI.addCheckboxGroup(len(allFilesInDir),2,allFilesInDir,[False]*len(allFilesInDir))

# Display the UI
whichFilesUI.showDialog()

# Initialize a list that will store all image files the user wanted to
# separate into fields of view
imgs2separate = []

# Loop across all image files found in the input directory
for fileInDir in allFilesInDir:

	# Check to see if the user specified that they want to process this
	# file
	if whichFilesUI.getNextBoolean():

		# If the user wanted to process this image, add it to our list
		imgs2separate.append(fileInDir)

del allFilesInDir, whichFilesUI, fileInDir

########################################################################
###### IDENTIFY WHICH MARKER (E.G. DAPI) WAS IMAGED IN EACH IMAGE ######
########################################################################

# Create a interface so that the user can specify what marker is imaged
# in each channel
whichMarkerUI = GenericDialog('Specify the marker (e.g. DAPI, NeuN) imaged in each file.')

# Loop across all selected image files
for imgPath in imgs2separate:

	# Get just the image file name separate from the path
	imgFile = os.path.basename(imgPath)

	# Add a row to UI so that user can indicate which marker the image
	# corresponds to
	whichMarkerUI.addStringField(imgFile,'DAPI',10)

# Display the UI
whichMarkerUI.showDialog()

# Store a list of all the markers corresponding to the images in
# imgs2separate
markersImaged = [whichMarkerUI.getNextString() for i in range(len(imgs2separate))]

del whichMarkerUI, imgPath, imgFile

########################################################################
###################### GENERATE FIELD OF VIEW ROIS #####################
########################################################################

# Construct a dummy ImagePlus object. For some reason, you need to do
# this before you can use the ImagePlus() construction to read image
# files
ImagePlus()

# Open the first image in our list of images we want to separate into
# fields of view
frst_img = ImagePlus(imgs2separate[0])

# Store the dimensions of this first image
frst_img_dims = frst_img.getDimensions()

# Separate the image into a grid-like configuration of fields of view
fovGrid = ROITools.gridOfFields(frst_img,field_size)

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
	'''

	# Crop the field of view from the larger image
	field = ROITools.getImgInROI(img2separate,fieldOfViewROI)

	# Normalize this field of view
	normalizedField = ImageProcessing.normalizeImg(field)

	# Save this field of view
	IJ.save(normalizedField,os.path.join(outDir,normalizedField.getTitle()))

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
	outDir = os.path.join(inputDir,'FieldsOfView',str(field_size) + 'pxlFields',markerInImg)

	# Create this output directory if necessary
	if not os.path.exists(outDir):
		os.makedirs(outDir)

	# Crop, normalize and save all fields of view from this image
	[crop_norm_save_fov(img2separate,fieldOfViewROI,outDir) for fieldOfViewROI in fovGrid.ROIs]

# Breakup the first image into separate fields of view
breakupIntoFields(frst_img,markersImaged[0])

# Delete the first image from memory
del frst_img

# Loop across all images whose fields of view need to be separated as
# well as their respective markers
for imgPath, marker in zip(imgs2separate[1:],markersImaged[1:]):

	# Read the image file into an ImagePlus object
	img = ImagePlus(imgPath)

	# Breakup the image into separate fields of view
	breakupIntoFields(img,marker)

	# Clear the current image from memory
	del img

del imgs2separate, markersImaged, frst_img_dims, imgPath, marker

########################################################################
######################## SAVE FIELD OF VIEW ROIS #######################
########################################################################

# Write a file path to where we want to save our set of Field of View
# ROIs
fieldROIsPath = os.path.join(inputDir,'ROIs',str(field_size) + 'pxlFields.zip')

# Save the field of view ROIs to this file path
ROITools.saveROIs(fovGrid.ROIs,fieldROIsPath)

del fieldROIsPath

# Write a file path to where we want to save our Field boundary ROI
fieldBoundaryROIPath = os.path.join(inputDir,'FieldsOfView',str(field_size) + 'pxlFields',str(field_size) + 'pxlFieldBoundary.roi')

del inputDir, field_size

# Save the field of view boundary ROI to this file path
ROITools.saveROIs(fovGrid.fieldBoundary,fieldBoundaryROIPath)

del fovGrid, fieldBoundaryROIPath
