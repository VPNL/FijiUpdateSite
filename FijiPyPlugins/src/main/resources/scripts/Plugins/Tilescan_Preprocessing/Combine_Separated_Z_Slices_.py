#@ File(label='Specify the folder containing the separate images from each channel and z-slice of your z-stack.',style='directory') separateSliceChannelFolder
#@ Boolean(label='Check this box if your image needs to be rotated and cropped.',value=True) needsRotation
#@ Short(label='Specify which channel in your image has the highest signal. This channel will be used to define the boundaries of the image to crop after rotation.',value=1) bestChannel

'''
Combine Separated Z Slices

This script will run a matlab function that will combine z slices from a
channel that has been separated by the Separate_Slices_Channels ImageJ
macros that is part of the Paredes-GrillSpectorLabs update site.

INPUTS

    - separateSliceChannelFolder (java.io.File): Path to the folder
                                 produced by the
                                 Separate_Slices_Channels macros
                                 containing separate tiff images from
                                 each channel and z-slice

    - needsRotation (Boolean): True if the image needs to be rotated and
                               cropped. Default = True

    - bestChannel (Int): Channel of the image that has the largest
                         signal. This channel will be used to define the
                         boundaries of the image to crop after rotation.
                         Defaults to first channel.

OUTPUTS This script will save final z-stacks for each image channel as
        separate tiff images in the directory above the
        separateSliceChannelFolder, where the larger composite image
        file you get from the microscope will reside.

AR Dec 2021
'''
########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so we can ask the user to specify the folder
# containing the separate tiff images from each channel and z-slice
from java.io import File

# Convert separateSliceChannelFolder from a java.io.File object to a
# string
separateSliceChannelDir = separateSliceChannelFolder.getAbsolutePath()
del separateSliceChannelFolder

# Import os so we can locate files and run shell commands
import os

########################################################################
########################## RUN MATLAB FUNCTION #########################
########################################################################

# Locate the location of our matlab script that will combine the z
# slices that were separated by the Separate_Slices-Channels ImageJ
# macros that is part of the Paredes-GrillSpectorLabs update site. This
# will be located in the scripts folder of the Fiji app.
scriptLocation = os.path.join(os.getcwd(),'scripts')

# Write out a command that will run our matlab function
command = 'matlab -nosplash -nodesktop -nojvm -r "addpath(genpath(\'' + scriptLocation + '\'));combineZSlices(\'' + separateSliceChannelDir + '\',\'' + str(needsRotation) + '\',\'' + str(bestChannel) + '\');"'

# Run the command
_ = os.system(command)
