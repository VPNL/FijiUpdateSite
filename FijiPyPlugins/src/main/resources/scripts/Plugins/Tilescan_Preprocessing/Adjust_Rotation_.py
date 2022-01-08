#@ File(label='Where is the folder containing the separate channels of the image you would like to manually rotate?',style='directory') input_dir
#@ Short(label='Which channel would you like to use to define your rotation?',value=4) channel4ManualRotation

'''
Adjust Rotation

This script can be used to manually adjust the rotation of tile scan
images so they are oriented the way the user desires. The maximum
intensity projection of one of the channels of the image will be
displayed to the user so that they can use Fiji's rotation function to
adjust the rotation of the image.

INPUTS

    - input_dir (java.io.File): Directory containing the separate
								channels of the image the user wanted to
                                adjust the rotation.

    - channel4ManualRotation (Int): Channel number that the user would
                                    like to use to adjust the rotation
                                    of all other channels

OUTPUTS

    After the user specifies the final desired rotation of the image,
    all channels of the image will be rotated accordingly and resaved.

AR Jan 2022
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so we can ask the user to specify the folder
# containing the images they would like to manually rotate
from java.io import File

# Convert the input_dir java.io.File object to a string so we know the
# path to the folder containing the images to be rotated
inputDir = input_dir.getAbsolutePath()
del input_dir

# Import ImagePlus so we can read image files
from ij import ImagePlus

# Construct a dummy ImagePlus object. For some reason, you need to do
# this before you can use the ImagePlus() construction to read image
# files
ImagePlus()

# Import our ImageProcessing module containing functions for rotating
# images, and the ImageFiles module containing functions for searching
# for image files.
from ImageTools import ImageFiles, ImageProcessing

########################################################################
############ OPEN THE IMAGE FILE WE WANT TO MANUALLY ROTATE ############
########################################################################

# Search the directory specified by the user to identify the image we'll
# use to specify the rotation
img2RotateFile = ImageFiles.findImgsInDir(inputDir,'tif',
                                          'c{}_'.format(channel4ManualRotation))

# Open the image that we want to rotate
img2Rotate = ImagePlus(img2RotateFile)

# Create a z-stack object for this image
img2RotateStack = ImageProcessing.zStack(img2Rotate)
del img2Rotate

# Generate the maximum intensity projection of the image we want to
# rotate
maxProj2Rotate = img2RotateStack.maxProj()
del img2RotateStack

# Ask the user to rotate this image, returning the angle of rotation
[_,rotAngle] = ImageProcessing.manualRotation(maxProj2Rotate)
