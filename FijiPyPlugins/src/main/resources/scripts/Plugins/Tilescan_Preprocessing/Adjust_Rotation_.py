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
								 channels of the image the user wanted
                                 to adjust the rotation.

    - channel4ManualRotation (Int): Channel number that the user would
                                    like to use to adjust the rotation
                                    of all other channels

OUTPUTS

    After the user specifies the final desired rotation of the image,
    all channels of the image will be rotated accordingly and saved
    under the same image file name with the prefix 'Rotated_' at the
    beginning.

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

# Import IJ so we can save image files
from ij import IJ

# Import our ImageProcessing module containing functions for rotating
# images, and the ImageFiles module containing functions for searching
# for image files.
from ImageTools import ImageFiles, ImageProcessing

# Import os so we can identify the file separator character used for
# this computer
import os

########################################################################
############ OPEN THE IMAGE FILE WE WANT TO MANUALLY ROTATE ############
########################################################################

# Search the directory specified by the user to identify the image we'll
# use to specify the rotation
img2RotateFile = ImageFiles.findImgsInDir(inputDir,'tif',
                                          'c{}_'.format(channel4ManualRotation))

# Open the image that we want to rotate as a virtual stack
img2Rotate = ImageFiles.openVirtualStack(img2RotateFile)
del img2RotateFile

# Create a z-stack object for this image
img2RotateStack = ImageProcessing.zStack(img2Rotate)

# Generate the maximum intensity projection of the image we want to
# rotate
maxProj2Rotate = img2RotateStack.maxProj()
img2Rotate.close()
del img2Rotate
img2RotateStack.orig_z_stack.close()
del img2RotateStack

########################################################################
######### IDENTIFY THE ANGLE THAT WE WANT TO ROTATE OUR IMAGES #########
########################################################################

# Ask the user to rotate this image, returning the angle of rotation
[imgRotated,rotAngle] = ImageProcessing.manualRotation(maxProj2Rotate)
maxProj2Rotate.close()
imgRotated.close()
del maxProj2Rotate, imgRotated

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

# Locate the location of the Paredes & Grill-Spector Labs' Matlab
# scripts
matScriptsPath = os.path.join(os.getcwd(),'scripts')

# Write out a command to rotate and save the image files
command = 'matlab -nosplash -nodesktop -nojvm -r "addpath(genpath(\'' + matScriptsPath + '\'));rotateAndSaveStacks(\'' + inputDir  + '\',\'' + str(rotAngle) + '\',\'' + str(channel4ManualRotation) + '\');"'

# Run the command
_ = os.system(command)
