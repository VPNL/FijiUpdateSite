'''
ImageDisplay Module

This module contains functions changing how images are displayed in Fiji

    overlayImages(imgs2merge)

        - Merges images so that they overlap with different colors

    getOpenImages()

        - Returns a list of all currently open images in Fiji

    openAsVirtualStack(imageFile)

        - Opens an image file into a virtual stack using Bio-Formats

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

# Import window manager so we can find images currently open in Fiji
from ij import WindowManager

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

    # Check to see if only two images are being overlaid
    if len(imgNames) < 3:

        # Indicate that we want the first image to be green and the
        # second magenta
        channels = [2,6]

    # If there are more images getting overlaid...
    else:

        # Store a list of all the channel numbers we want to use in
        # descending order of preference (cyan, magenta, yellow, gray,
        # green, blue, red)
        channels = [5,6,7,4,2,3,1]

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

########################################################################
############################# getOpenImages ############################
########################################################################

# Define a function to get all images currently open in Fiji
def getOpenImages():
    '''
    Returns a list of all currently open images in Fiji

    getOpenImages()

    OUTPUT List of Fiji ImagePlus objects, one for each image currently
           open in Fiji. If only one image is open, return just that
           ImagePlus object rather than a list.

    AR Dec 2021
    '''

    # Check to see if any images are open
    if WindowManager.getIDList() is None:

        # Return none if there are no images currently open
        return None

    # Get all images currently open
    open_images = [WindowManager.getImage(id) for id in WindowManager.getIDList()]

    # If there is only one open image
    if len(open_images) == 1:

        # Just return the image, not in a list
        return open_images[0]

    # If there are multiple images open
    else:

        # Return list of all open images
        return open_images

########################################################################
############################# getOpenImages ############################
########################################################################

# Define a function that will read image files into virtual stacks
def openAsVirtualStack(imageFile):
    '''
    Opens an image file into a virtual stack using Bio-Formats

    openAsVirtualStack(imageFile)

        - imageFile (String): File path to the location of the image you
                              want to open

    OUTPUT Opened image as an ImagePlus object

    AR May 2022
    '''

    # Read the image file into a virtual stack
    IJ.run("Bio-Formats",
          "open=[{}] color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT use_virtual_stack".format(imageFile))

    # Grab the newly opened image
    img = getOpenImages()

    # Check to see if multiple images were opened
    if isinstance(img,list):

        # Return just the most recently opened image
        return img[-1]

    # Otherwise ...
    else:

        # ... return the only open image
        return img
