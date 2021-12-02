'''
ImageDisplay Module

This module contains functions changing how images are displayed in Fiji

    overlayImages(imgs2merge)

        - Merges images so that they overlap with different colors

'''

########################################################################
############################ IMPORT PACKAGES ###########################
########################################################################

# Add Fjij's duplicator package so we can duplicate images
from ij.plugin import Duplicator

# Initialize a duplicator object
duplicator = Duplicator()

# Import IJ so we can run Fiji macros commands
from ij import IJ

# Import izip so we can iterate across multiple lists
from itertools import izip

########################################################################
############################# overlayImages ############################
########################################################################

# Define a function to overlay images as separate color channels
def overlayImages(imgs2merge):
    '''
    Merges images so that they overlap with different colors

    overlayImages(imgs2merge)

        - imgs2merge (List of Fiji ImagePlus): Images you want to merge
                                               into separate color
                                               channels

    OUTPUT Fiji ImagePlus object containing the merged image. The order
    of the images in imgs2merge determines their final color according
    to this order: green, magenta, blue, gray, yellow, cyan, red

    AR Nov 2021
    '''

    # Copy each image
    imgs2merge_cp = [duplicator.run(img) for img in imgs2merge]

    # Display each image
    [img.show() for img in imgs2merge_cp]

    # Store a list of all of the image names
    imgNames = [img.getTitle() for img in imgs2merge_cp]

    # Store a list of all the channel numbers we want to use in
    # descending order of preference (green, magenta, blue, gray,
    # yellow, cyan, red)
    channels = [2,6,3,4,7,5,1]

    # Merge the images, assigning each image a color based on our
    # ordering
    IJ.run('Merge Channels...',
           ' '.join('c%s=%s' % channel for channel in izip(channels[:len(imgNames)],imgNames)) + ' create')

    # The overlay will be the currently open ImageJ image. Store this
    # image as a variable.
    overlay =  IJ.getImage()

    # Hide the overlay in case the user doesn't want to see it right
    # away
    overlay.hide()

    # Close out the duplicated images
    [img.close() for img in imgs2merge_cp]

    # Return the overlaid image
    return overlay
