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

    segmentation2ROIs(seg)

        - Converts a segmentation, for instance of a nuclear stain, into
          a set of ROIs

    ROIs2Segmentation(ROIs,refImg)

        - Converts a list of ROIs into a segmentation mask

    manualRotation(img)

        - Ask the user to rotate an image manually, returns angle of
          rotation

    autoRotation(img,angle)

        - Automatically rotates an image by a set angle

'''

########################################################################
############################ IMPORT PACKAGES ###########################
########################################################################

# Import the ZProjector so we can perform maximum intensity projections
# and the Duplicator so we can duplicate ImagePlus objects
from ij.plugin import ZProjector, Duplicator

# Initialize instance of ZProjector and Duplicator
zprojector = ZProjector()
duplicator = Duplicator()

# Import Fiji's contrast enhancement package
from ij.plugin import ContrastEnhancer

# Import IJ so we can run macros commands
from ij import IJ, ImagePlus

# Import floor from math so we can round down
from math import floor

# Import GaussianBlur class so we can smooth images, and Rotator so we
# can rotate images
from ij.plugin.filter import GaussianBlur, Rotator

# Initialize a rotator object
rotator = Rotator()

# Import a generic dialog so we can display messages to the user
from ij.gui import GenericDialog

# Import ROI Tools so we can work with Fiji ROIs
import ROITools

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

        - cropZStack(slices): Method that will return a z-stack
                              containing only the desired z-slices

    AR Oct 2021
    AR Nov 2021, added setZLevels4Focus and cropZStack methods
    AR Dec 2021, renamed images after they are cropped
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

    # Define a method to crop the z-stack so that only the desired
    # z-slices are present
    def cropZStack(self,slices=None):
        '''
        Method that will return a z-stack containing only the desired
        z-slices

        cropZStack(slices)

            - slices (Int): The total number of z-slices you want to be
                            included in your final list of z-levels to
                            be focused on.

        cropZStack(slices)

            - slices (List of 2 Ints): The starting and ending z-levels
                                       for the z-stack you want.

        OUTPUT (Fiji ImagePlus) z-stack cropped to only contain the
                                desired z-slices

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

        # Check to see if the user specified across how many slices they
        # would like to include in the final z-stack
        if all([slices is None, not hasattr(self,'starting_z_included'),
                not hasattr(self,'ending_z_included')]):

            # If no number of slices were included, return the full
            # z-stack
            return duplicator.run(self.orig_z_stack)

        # If the user has at some point specified the number of slices
        # to be included...
        else:

            # Check to see if slices was defined
            if slices is not None:

                # Set the starting and ending slices to be included in
                # the max projection
                self.setZLevels4Focus(slices)

            # Get a copy of the z-stack including only our desired
            # z-slices
            cropped_img = duplicator.run(self.orig_z_stack,
                                        self.starting_z_included,
                                        self.ending_z_included)

            # Rename the cropped image so that it's the same as the
            # original z stack
            cropped_img.setTitle(self.orig_z_stack.getTitle())

            # Return this cropped image
            return cropped_img

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
    z_stack = duplicator.run(img)

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
    gausBlur = duplicator.run(img)

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

########################################################################
########################### segmentation2ROIs ##########################
########################################################################

# Define a function to convert a segmentation image into a list of
# separate ROIs for each segmented object
def segmentation2ROIs(seg):
    '''
    Converts a segmentation, for instance of a nuclear stain, into a set
    of ROIs

    segmentation2ROIs(seg)

        - seg (Fiji ImagePlus): Segmentation image you want to convert
                                to ROIs

    OUTPUT List of Fiji ROI objects with separate ROIs for each
           segmented object

    AR Nov 2021
    '''

    # Make a copy of this segmented image
    seg_cp = duplicator.run(seg)

    # Compute the pixel statistics for our segmentation image. This will
    # help us set an appropriate threshold for the image.
    seg_stats = seg_cp.getStatistics()

    # Display the segmentation
    seg_cp.show()

    # Set a threshold for the segmentation making sure to label
    # everything that was segmented, in case the wrong color was used
    # when editing the segmentation.
    IJ.setThreshold(seg_cp, seg_stats.min + 1, seg_stats.max)

    # Convert the threshold to a mask
    IJ.run('Convert to Mask')

    # Clear ROIs from the ROI Manager
    ROITools.clearROIs()

    # Run the particle analyzer to separate the segmentation into
    # distinct ROIs for each object in your image
    IJ.run(seg_cp, "Analyze Particles...", "add")

    # Close our copy of the segmentation
    seg_cp.close()

    # Store a list of all of the distinct ROIs drawn on this
    # segmentation
    segROIs = ROITools.getOpenROIs()

    # Clear these ROIs from the ROI Manager
    ROITools.clearROIs()

    # Return the final list of ROIs
    return segROIs

########################################################################
########################### ROIs2Segmentation ##########################
########################################################################

# Define a functiont that will produce a segmentation mask from a list
# of ROIs
def ROIs2Segmentation(ROIs,refImg):
    '''
    Converts a list of ROIs into a segmentation mask

    ROIs2Segmentation(ROIs,refImg)

        - ROIs (List of Fiji ROIs): List of ROIs you want included in
                                    your segmentation mask

        - refImg (Fiji ImagePlus): Reference image that has the same
                                   dimensions as your final segmentation
                                   mask

    OUTPUT Fiji ImagePlus containing your final segmentation mask

    AR Nov 2021
    '''

    # Combine all of the ROIs into a composite ROI
    combinedROI = ROITools.combineROIs(ROIs)

    # Superimpose the ROI on top of the reference image
    refImg.setRoi(combinedROI)

    # Generate the segmentation mask
    segImg = ImagePlus('Segmentation_' + refImg.getTitle(),
                       refImg.createRoiMask())

    # Return this segmentation mask
    return segImg

########################################################################
############################ manualRotation ############################
########################################################################

# Define a function so that the user can adjust the rotation of an image
def manualRotation(img):
    '''
    Ask the user to rotate an image manually, returns angle of rotation

    manualRotation(img):

        - img (ImagePlus): Image you want to rotate

    OUTPUT list of two elements. The first element is the rotated image.
    the second element is the angle that the image was rotated.

    AR Dec 2021

    AR Jan 2022: Switched order so that the log appears before the image
                 Enhance contrast of the image to be rotated
    '''

    # Hide the image provided so that it doesn't get confused with the
    # copy we will make of it
    img.hide()

    # Copy the image provided
    img_cp = duplicator.run(img)

    # Set the image name to the same as the original image file
    img_cp.setTitle(img.getTitle())

    # Display the copied image
    img_cp.show()

    # Enhance the contrast of the displayed image.
    ContrastEnhancer().stretchHistogram(img_cp,.35)

    # Instruct ImageJ to rotate the currently opened image 0 degrees. By
    # doing this, we can set the default values for the angle, grid
    # size, interpolation and make sure fill and enlarge are both
    # checked off
    IJ.run("Rotate... ","angle=0 grid=0 interpolation=Bilinear fill enlarge")

    # Initialize a GUI to give the user instructions
    gui = GenericDialog('Instructions')

    # Display a message to the user in the ImageJ log instructing them
    # to use the "preview" functionality to find the best angle for the
    # image, then press "OK"
    gui.addMessage('Use the preview option to identify the best angle to\nrotate your image.')

    # Display the gui
    gui.showDialog()

    # Display the rotator object to the user
    IJ.run("Rotate... ")

    # Get the angle that the image was rotated in degrees
    rotAngle = rotator.getAngle()

    # Hide the copied image
    img_cp.hide()

    # Return the final rotated image and the angle of rotation
    return [img_cp,rotAngle]

########################################################################
############################# autoRotation #############################
########################################################################

# Define a function to automatically rotate images
def autoRotation(img,angle):
    '''
    Automatically rotates an image by a set angle

    autoRotation(img,angle)

        - img (ImagePlus): Image you want to rotate

        - angle (float): How much you want to rotate the image in
                         degrees

    OUTPUTS Rotated image as an ImagePlus object

    AR Jan 2022
    '''

    # Hide the image provided so that it doesn't get confused with the
    # copy we will make of it
    img.hide()

    # Copy the image provided
    img_cp = duplicator.run(img)

    # Set the image name to the same as the original image file
    img_cp.setTitle(img.getTitle())

    # Display the copied image
    img_cp.show()

    # Rotate the image
    IJ.run("Rotate... ",
           "angle={} grid=0 interpolation=Bilinear fill enlarge stack".format(angle))

    # Return the rotated image as an ImagePlus
    return img_cp
