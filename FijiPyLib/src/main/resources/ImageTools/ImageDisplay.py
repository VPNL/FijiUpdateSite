'''
ImageDisplay Module

This module contains functions changing how images are displayed in Fiji

    overlayImages(greenImg,magentaImg)

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

########################################################################
############################# overlayImages ############################
########################################################################

# Define a function to overlay images as separate color channels
def overlayImages(greenImg,magentaImg,blueImg=None,whiteImg=None):
    '''
    Merges images so that they overlap with different colors

    overlayImages(greenImg,magentaImg)

        - greenImg (Fiji ImagePlus): Image you want to appear as green
                                     in overlay

        - magentaImg (Fiji ImagePlus): Image you want to appear as
                                       magenta in overlay

    OUTPUT Fiji ImagePlus object containing the merged image with two
    channels

    overlayImages(greenImg,magentaImg,blueImg,whiteImg)

        - greenImg (Fiji ImagePlus): Image you want to appear as green
                                     in overlay

        - magentaImg (Fiji ImagePlus): Image you want to appear as
                                       magenta in overlay

        - blueImg (Fiji ImagePlus): OPTIONAL Image you want to appear as
                                    blue in the overlay. If None
                                    provided, the blue channel will not
                                    be used

        - whiteImg (Fiji ImagePlus): OPTIONAL image you want to appear
                                     as white in the overlay. If None
                                     provided, the white channel will
                                     not be used

    OUTPUT Fiji ImagePlus object containing the merged image with four
    channels

    AR Nov 2021
    '''

    # Copy each image
    greenImg_cp = duplicator.run(greenImg)
    magentaImg_cp = duplicator.run(magentaImg)


    # Display each of these images
    greenImg_cp.show()
    magentaImg_cp.show()

    # Check to see if blue and white images were provided as well
    if blueImg is not None and whiteImg is not None:

        # Copy and display each image
        blueImg_cp = duplicator.run(blueImg)
        blueImg_cp.show()
        whiteImg_cp = duplicator.run(whiteImg)
        whiteImg_cp.show()

        # Create a four channel overlay
        IJ.run('Merge Channels...', 'c2=' + greenImg_cp.getTitle() + ' c3=' + blueImg_cp.getTitle() + ' c4=' + whiteImg_cp.getTitle() + ' c6=' + magentaImg_cp.getTitle() + ' create')

        # Close the duplicated blue and white images
        blueImg_cp.close()
        whiteImg_cp.close()

    # If no blue and white images were provided...
    else:

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
