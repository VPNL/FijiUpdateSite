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

    smoothImg(img)

        - Automatically smooths image using Fiji's Gaussian Blur Plugin

    segmentImg(img)

        - Automatically segments an image using Fiji's Statistical
          Region Merging plugin

'''

########################################################################
############################ IMPORT PACKAGES ###########################
########################################################################

# Import the ZProjector so we can perform maximum intensity projections
# and the Duplicator so we can duplicate ImagePlus objects
from ij.plugin import ZProjector, Duplicator

# Initialize instance of ZProjector
zprojector = ZProjector()

# Import Fiji's contrast enhancement package
from ij.plugin import ContrastEnhancer

# Import IJ so we can run macros commands
from ij import IJ

# Import floor from math so we can round down
from math import floor

# Import GaussianBlur class so we can smooth images
from ij.plugin.filter import GaussianBlur

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

        - setZLevels4Focus(slices): Method that will return the starting
                                    and ending z-levels to be focused
                                    on. If a number of slices is
                                    provided by the user, this method
                                    will choose this number of z-levels
                                    surrounding the center for focusing.
                                    If a list of two slice numbers is
                                    provided directly by the user, these
                                    will be used as the z-levels for
                                    focusing.

        - maxProj(slices): Method that will return a maximum intensity
                           projection across only the desired number of
                           z-slices

        - TODO cropZStack(nSlices): Method that will return a z-stack
                               containing only the desired number of
                               z-slices


    AR Oct 2021
    AR Nov 2021, added setZLevels4Focus method
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

    # Define a method that will return some specified number of z-levels
    # surrounding the center of the z-stack
    def setZLevels4Focus(self,slices):
        '''
        Method that will return the starting and ending z-levels to be
        focused on. If a number of slices is provided by the user, this
        method will choose this number of z-levels surrounding the
        center for focusing. If a list of two slice numbers is provided
        directly by the user, these will be used as the z-levels for
        focusing.

        setZLevels4Focus(slices)

            - slices (Int): The total number of z-slices you want to be
                            included in your final list of z-levels to
                            be focused on.

        setZLevels4Focus(slices)

            - slices (List of 2 Ints): The starting and ending z-levels
                                       for the z-stack you want.

        ATTRIBUTES added

            - centralSlice (Int): Slice number at the center of the
                                  z-stack.

            - starting_z_included (Int): The starting z-slice included
                                         in the calculation of the max
                                         projection

            - ending_z_included (Int): The ending z-slice included in
                                       the calculation of the max
                                       projection

        AR Nov 2021
        '''

        # Check to see if the staring and ending z-levels of the z-stack
        # were directly provided by the user
        if isinstance(slices,(list,tuple)):

            # Store the starting and ending slice as attributes of this
            # object
            self.starting_z_included = slices[0]
            self.ending_z_included = slices[-1]

            # Finish this method without returning anything
            return

        # Halve the desired number of slices, rounding down
        half_nSlices = int(floor(float(slices)/2.0))

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
            return

        # Store the starting and ending slice that will be included
        # in the maximum intensity projection
        self.starting_z_included = int(self.centralSlice - half_nSlices)
        self.ending_z_included = int(self.centralSlice + half_nSlices)

        # Return the starting and ending z-levels
        return [self.starting_z_included,self.ending_z_included]

    # Define a method to build a maximum intensity projection using only
    # slices where we expect there to be stain
    def maxProj(self,slices=None):
        '''
        Method that will produce a maximum intensity projection,
        focusing only on slices where we expect the stain to have
        penetrated

        maxProj(slices)

            - slices (Int): The total number of z-slices you want to be
                            included in your final list of z-levels to
                            be focused on.

        maxProj(slices)

            - slices (List of 2 Ints): The starting and ending z-levels
                                       for the z-stack you want.

        OUTPUT (Fiji ImagePlus) Maximum intensity projection. If the
                                center of the stack is too close to the
                                edges of the z-stack, returns None

        ATTRIBUTES added

            - centralSlice (Int): Slice number at the center of the
                                  z-stack.

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
        if all([slices is None, not hasattr(self,'starting_z_included'),
               not hasattr(self,'ending_z_included')]):

            # If the number of slices wasn't specified, compute the max
            # projection across all slices in the image. Return this
            # projection
            return zprojector.run(self.orig_z_stack,'max')

        # If the user specified the slices across which to perform the
        # max projection
        else:

            # Set the starting and ending slices to be included in the
            # max projection
            self.setZLevels4Focus(slices)

            # Compute and return the maximum intensity projection across
            # the z-slices that we wanted to focus on
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

########################################################################
############################### smoothImg ##############################
########################################################################

# Define a function to smooth images
def smoothImg(img,radius=6):
    '''
    Automatically smooths image using Fiji's Gaussian Blur Plugin.

    smoothImg(img,radius)

        - img (Fiji ImagePlus): Single z-plane image you want to smooth

        - radius (Int or Float): Radius of the Gaussian filter you want
                                 to use for smoothing (default = 6)

    OUTPUTS blurred image as a Fiji ImagePlus object

    AR Nov 2021
    '''

    # Duplicate the image so that we don't edit it directly. This image
    # will later be smoothed using a Gaussian blur
    gausBlur = Duplicator().run(img)

    # Rename this image so that the user knows it is a blurred image
    gausBlur.setTitle('Gaussian_Blur_{}'.format(img.getTitle()))

    # Smooth the image using a Gaussian filter of specified radius
    GaussianBlur().blurGaussian(gausBlur.getProcessor(),radius)

    # Return the smoothed image
    return gausBlur

########################################################################
############################## segmentImg ##############################
########################################################################

# Define a function to segment an image
def segmentImg(img,gausRadius=6,q=17,autoThreshMethod='Mean dark'):
    '''
    Automatically segments an image using Fiji's Statistical Region
    Merging plugin.

    segmentImg(img)

        - img (Fiji ImagePlus): Single z-plane image you would like to
                                segment

        - gausRadius (Int or Float): Radius of the Gaussian filter you
                                     want to use for smoothing the
                                     image before segmenting. (default
                                     = 6)

        - q (Int): Parameter used for the Statitical Region Merging
                   Plugin. It is a rough estimate of the number of
                   regions in the image (default = 17)

        - autoThreshMethod (String): Method of Fiji's automated
                                     thresholding plugin to use (default
                                     = 'Mean dark')

    OUTPUTS segmented image as a Fiji ImagePlus object

    AR Nov 2021
    '''

    # Get a smoothed version of that image
    smoothedImg = smoothImg(img,gausRadius)

    # Run the statitical region merging algorithm on this blurred image
    IJ.run(smoothedImg,'Statistical Region Merging','q={} showaverages'.format(q))

    # As a result of running the statistical region merging algorithm, a
    # new image will pop up with the resulting segmented image. Grab
    # this new image.
    regMergImg = IJ.getImage()

    # Next we'll want to use Fiji's automated thresholding algorithm to
    # binarize this region merging segmentation. However, Fiji's
    # automated thresholding algorithm only support 8 or 16 bit images.
    # Check to see the bit depth of our current image
    if regMergImg.getBitDepth() in (8,16):

        # If the image is not 8 or 16 bit, convert to 16 bit
        IJ.run('16-bit')

    # Make sure Fiji knows that we want the background of our final
    # segmentation to be black
    IJ.run("Options...", "iterations=1 count=1 black do=Nothing")

    # Use Fiji's automated thresholding algorithm to binarize this
    # segmentation
    IJ.setAutoThreshold(regMergImg,autoThreshMethod)

    # Convert this threshold into a mask
    IJ.run('Convert to Mask')

    # Finally, clean up the segmentation using quick binary commands
    IJ.run("Dilate")
    IJ.run("Close-")
    IJ.run("Fill Holes")
    IJ.run("Erode")
    IJ.run("Watershed")

    # Hide this new image from view so we're not overwhelmed with popups
    regMergImg.hide()

    # Rename the image to specify what it was segmenting
    regMergImg.setTitle('Segmented_{}'.format(img.getTitle()))

    # Return this final segmented image
    return regMergImg
