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

# Import ImagePlus so we can read image files and IJ so we can save them
from ij import ImagePlus, IJ

# Construct a dummy ImagePlus object. For some reason, you need to do
# this before you can use the ImagePlus() construction to read image
# files
ImagePlus()

# Import our ImageProcessing module containing functions for rotating
# images, and the ImageFiles module containing functions for searching
# for image files.
from ImageTools import ImageFiles, ImageProcessing

# Import os so we can identify the file separator character used for
# this computer
import os

# Import positive integer object from bio-formats so we can specify
# image dimensions
from ome.xml.model.primitives import PositiveInteger

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

########################################################################
######### IDENTIFY THE ANGLE THAT WE WANT TO ROTATE OUR IMAGES #########
########################################################################

# Ask the user to rotate this image, returning the angle of rotation
[_,rotAngle] = ImageProcessing.manualRotation(maxProj2Rotate)

# Search the directory specified by the user to identify the text file
# containing the final angle of rotation of our images
rotAngleTextFilePath = ImageFiles.findImgsInDir(inputDir,'txt',
                                                'RotationInDegrees_')

# Open the text file
with open(rotAngleTextFilePath,'r+') as rotAngleTextFile:

    # Read the angle currently saved in the text file
    currRot = float(rotAngleTextFile.read())

    # Set the current position in the file to the start
    rotAngleTextFile.seek(0)

    # Add our manual rotation angle with the current rotation and write
    # final angle to text file
    rotAngleTextFile.write(str(currRot + rotAngle))

    # Close the file
    rotAngleTextFile.close()
del rotAngleTextFilePath, rotAngleTextFile, currRot

########################################################################
################## READ, ROTATE AND RESAVE ALL IMAGES ##################
########################################################################

# Get a list of all image files that we want to rotate
imgFiles2Rotate = ImageFiles.findImgsInDir(inputDir,'tif','c\d_')

# Store ImageJ's version number
FijiVersion = IJ.getVersion()

# The only part of the version number we care about comes after a '/'
# character. Crop the string to include just these characters.
FijiVersion = FijiVersion[FijiVersion.index('/')+1:]

# Rotate across all image files
for imgFile2Rotate in imgFiles2Rotate:

    # Read the image file
    img2Rotate = ImagePlus(imgFile2Rotate)

    # Get the pixel units for this image
    imgUnits = img2Rotate.getCalibration().getUnit()

    # Rotate the image file
    rotatedImg = ImageProcessing.autoRotation(img2Rotate,rotAngle)
    del img2Rotate

    # Get the meta data for this image
    imgMetaData = ImageFiles.getOMEXMLMetadata(imgFile2Rotate)

    # Update the dimensions of the image stored in the meta data to
    # match our rotated image
    imgMetaData.setPixelsSizeX(PositiveInteger(rotatedImg.getWidth()),0)
    imgMetaData.setPixelsSizeY(PositiveInteger(rotatedImg.getHeight()),0)

    # Add the image description to the meta data to make it easier to
    # read into ImageJ
    imgDescription = "ImageJ=%s\nunit=%s\n" % (FijiVersion, imgUnits)
    imgMetaData.setImageDescription(imgDescription,0)

    # Delete the current image file so we can re-write it
    os.remove(imgFile2Rotate)

    # Save our rotated image with this meta data to the same image file
    ImageFiles.saveCompressedImg(rotatedImg,imgMetaData,imgFile2Rotate)
    rotatedImg.hide()
    del rotatedImg, imgMetaData
