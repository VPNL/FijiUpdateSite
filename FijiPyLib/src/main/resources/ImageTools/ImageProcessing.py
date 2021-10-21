'''
ImageProcessing Module

This module contains tools to process images in Fiji.

    zStack(img)

        - Class of objects that works with z-stacks, for instance
          generating maximum intensity projections, or identifing the
          center of the stack, or cropping the stack around the central
          z-slices.

    normalizeImg(img)

        - Automatically adjusts the brightness/contrast of an image and
          performs a histogram normalization

'''

########################################################################
############################ IMPORT PACKAGES ###########################
########################################################################

# Import Fiji's z projection module so we can generate max intensity
# projections
from ij.plugin import ZProjector

# Import Fiji's contrast enhancement package
from ij.plugin import ContrastEnhancer

# Import IJ so we can run macros commands
from ij import IJ

# Import the ZProjector so we can perform maximum intensity projections
# and the Duplicator so we can duplicate ImagePlus objects
from ij.plugin import ZProjector, Duplicator

# Initialize instance of ZProjector
zprojector = ZProjector()

# Import floor from math so we can round down
from math import floor

########################################################################
################################ zStack ################################
########################################################################

# Define a class of objects that will perform methods on z-stacks
class zStack:
    '''
    Class of objects that works with z-stacks, for instance generating
    maximum intensity projections, or identifing the center of the
    stack, or cropping the stack around the central z-slices.

    ATTRIBUTES

        - orig_z_stack (Fiji ImagePlus): Original z-stack to be
                                         projected

    METHODS

        - centerOfStack(): Method that will return the slice identified
                           as the center of the z-stack

        - maxProj(nSlices): Method that will return a maximum intensity
                            projection across only the desired number of
                            z-slices

        - TODO cropZStack(nSlices): Method that will return a z-stack
                               containing only the desired number of
                               z-slices


    AR Oct 2021
    '''

    # Initialize object
    def __init__(self,img):
        '''
        zStack(img)

            - img (Fiji ImagePlus): Z-Stack for the maximum intensity
                                    projection

        AR Oct 2021
        '''

        # Store the original z-stack that will be projected
        self.orig_z_stack = img

    # Define a method that will be used to identify the central slice of
    # the z-stack
    def centerOfStack(self):
        '''
        Method that will return the slice identified as the center of
        the z-stack. The center here is defined as the slice with the
        highest average pixel intensity.

        OUTPUT (Int) slice number at the center of the z-stack. Adds
                     this slice number as the attribute 'centralSlice'

        AR Oct 2021
        '''

        # Store the total number of z-slices in the image
        nSlices = self.orig_z_stack.getNSlices()

        # Create a list that will store the average gray level at each
        # slice
        pxl_avgs = []

        # Loop across all slices of the image
        for s in range(1,nSlices + 1):

            # Change the current slice in the image
            self.orig_z_stack.setSliceWithoutUpdate(s)

            # Store the average pixel intensity at this slice in our
            # listpxl_avgs
            pxl_avgs.append(self.orig_z_stack.getStatistics().mean)

        # Store this slice number as an attribute for the object
        self.centralSlice = pxl_avgs.index(max(pxl_avgs)) + 1

        # Return the slice number with the largest average pixel
        # intensity
        return self.centralSlice

    # Define a method to build a maximum intensity projection using only
    # slices where we expect there to be stain
    def maxProj(self,nSlices=None):
        '''
        Method that will produce a maximum intensity projection,
        focusing only on slices where we expect the stain to have
        penetrated

        maxProj(nSlices)

            - nSlices (Int): The total number of z-slices you want to be
                             included in the calculation of the maximum
                             intensity projection. Optional, defaults to
                             the total number of z-slices in the z-stack

        OUTPUT (Fiji ImagePlus) Maximum intensity projection. If the
                                center of the stack is too close to the
                                edges of the z-stack, returns None

        ATTRIBUTES added

            - starting_z_included (Int): The starting z-slice included
                                         in the calculation of the max
                                         projection

            - ending_z_included (Int): The ending z-slice included in
                                       the calculation of the max
                                       projection

        AR Oct 2021
        '''

        # Check to see if the user specified across how many slices they
        # would like to compute the projection
        if nSlices is None:

            # If the number of slices wasn't specified, compute the max
            # projection across all slices in the image. Return this
            # projection
            return zprojector.run(self.orig_z_stack,'max')

        # If the user specified the number of slices across which to
        # perform the max projection
        else:

            # Halve this number of slices
            half_nSlices = int(floor(float(nSlices)/2.0))

            # Check to see we've already computed the central slice of
            # this z-stack
            if not hasattr(self,'centralSlice'):

                # If the central slice attribute hasn't been computed,
                # compute it now
                self.centerOfStack()

            # Make sure the central z-plane isn't too close to the edges
            # of the z-stack
            if self.centralSlice < half_nSlices + 1 or self.centralSlice > self.orig_z_stack.getNSlices() - half_nSlices:

                # If the central slice is too close to the edges, return None
                return None

            # Store the starting and ending slice that will be included
            # in the maximum intensity projection
            self.starting_z_included = int(self.centralSlice - half_nSlices)
            self.ending_z_included = int(self.centralSlice + half_nSlices)

            # Compute and return the maximum intensity projection across
            # the z-slices
            return zprojector.run(self.orig_z_stack,'max',self.starting_z_included,self.ending_z_included)

########################################################################
############################ normalizeImg ##############################
########################################################################

# Define a function to normalize images
def normalizeImg(img):
    '''
    Automatically adjusts the brightness/contrast of an image and
    performs a histogram normalization.

    normalizeImg(img)

        - img (Fiji ImagePlus): Image you would like to normalize

    OUTPUTS normalized image as a Fiji ImagePlus object

    AR Oct 2021
    '''

    # Duplicate the input z-stack
    z_stack = Duplicator().run(img)

    # Compute the maximum intensity projection of our image using the
    # zStack object
    imgStack = zStack(z_stack)
    maxProjection = imgStack.maxProj()

    # Enhance the contrast of the maximum intensity projection. The .35
    # is Fiji's default value for the parameter called "saturated" that
    # controls what proportion of pixels become saturated by the
    # contrast adjustment
    ContrastEnhancer().stretchHistogram(maxProjection,.35)

    # Get the minimum and maximum value calculated for the ideal
    # contrast adjustment
    min4contrast = maxProjection.getDisplayRangeMin()
    max4contrast = maxProjection.getDisplayRangeMax()

    # Use the contrast range from the maximum intensity projection to
    # adjust the dynamic range of the full z-stack
    z_stack.setDisplayRange(min4contrast,max4contrast)
    IJ.run(z_stack,'Apply LUT', 'stack')

    # Reset the name of z_stack to match the original image
    z_stack.setTitle(img.getTitle())

    # Return the normalized z-stack
    return z_stack
