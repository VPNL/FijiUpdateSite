'''
ImageDisplay Module

This module contains functions changing how images are displayed in Fiji

    overlayImages(greenImg,magentaImg)

        - Merges two images so that they overlap with different colors

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

########################################################################
############################# overlayImages ############################
########################################################################

# Define a function to overlay two images as separate color channels
def overlayImages(greenImg,magentaImg):
    '''
    Merges two images so that they overlap with different colors

    overlayImages(greenImg,magentaImg)

        - greenImg (Fiji ImagePlus): Image you want to appear as green
                                     in overlay

        - magentaImg (Fiji ImagePlus): Image you want to appear as
                                       magenta in overlay

    OUTPUT Fiji ImagePlus object containing the merged image

    AR Nov 2021
    '''

    # Copy each image
    greenImg_cp = duplicator.run(greenImg)
    magentaImg_cp = duplicator.run(magentaImg)

    # Display each of these images
    greenImg_cp.show()
    magentaImg_cp.show()

    # Create an overlay using these duplicated images
    IJ.run('Merge Channels...', 'c2=' + greenImg_cp.getTitle() + ' c6=' + magentaImg_cp.getTitle() + ' create')

    # The overlay will be the currently open ImageJ image. Store this
    # image as a variable.
    overlay =  IJ.getImage()

    # Hide the overlay in case the user doesn't want to see it right
    # away
    overlay.hide()

    # Close out the duplicated images
    greenImg_cp.close()
    magentaImg_cp.close()

    # Return the overlaid image
    return overlay
