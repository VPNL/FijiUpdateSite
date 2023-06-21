'''
ROITools Module

This module contains tools to work easily with Fiji ROIs

    gridOfFields(img,field_size,field_overlap,isRotated)

        - Class of objects that will divide up an image into a grid-like
          set of fields of view, where each field overlaps 50% into its
          neighbors. Stores the following attributes:

            * ROIs (list of Fiji ROIs): A list of square ROIs
              corresponding to separate fields of view sampled in a
              grid-like manner across an image. These ROIs will be twice
              the size of field_size and overlap 50% into the
              neighboring fields of view.

            * fieldBoundary (Fiji ROI): Each ROI listed under the ROIs
              attribute overlaps 50% into its neighboring fields of
              view. When any of these fields are isolated, you can use
              this ROI to denote the true boundary of the field of view.

    selectNonBlackRegion(img)

        - Makes an ROI just around the non-black region of the image

    cleanUpROI(ROI)

        - Removes loose overhangs from ROIs

    makeRotatedR0I(topLeftPoint,width,rotation)

        - Makes rotated ROIs

    getTopLeftPoint(ROI)

        - Returns the top left point of an ROI

    isContained(containedROI,containingROI)

        - Check to see if one region is contained within another

    subtractROI(TotalRegion,Region2Remove)

        - Function that will subtract one ROI from another

    getIntersectingROI(ROIs)

        - Function that will return the intersection of a list of ROIs

    getImgInROI(img,ROI)

        - Function that will return the portion of an image contained
          within an ROI

    getOpenROIs()

        - Function that will return all ROIs in the ROI Manager

    addROIs2Manager(ROIs)

        - Function that will add Fiji ROIs to the Fiji ROI Manager

    saveROIs(ROIs,outFilePath)

        - Function that will save either singular or sets of ROIs to a
          file

    openROIFile(ROIFile)

        - Function that will open and ROI File and return all ROIs that
          were saved

    clearROIs()

        - Function that clears all of the ROIs in the ROI Manager

    ROIsInArea(ROIs2Check,AreaContainingROIs)

        - Function that will check whether each ROI in a list of ROIs
          is contained within a given area of an image

    getROIArea(ROI,img)

        - Function that will compute the area of an ROI in physical
          units (e.g., microns) instead of just pixel units

    combineROIs(ROIs)

        - Function that will combine a set of ROIs into a single
          composite

    getBackgroundROI(nucROIs,fieldROI)

        - Function that will compute an ROI representing all pixels that
          were not segmented as part of nuclei

    computeSNR(ROIs,backgroundROI,img)

        - Function that will compute the signal to noise ratio (SNR) of
          the gray level inside a signal ROI compared to a background
          ROI

    grayLevelTTest(ROIs,ROI2Compare,img)

        - Function that will compute the t-statistic comparing the gray
          level inside each ROI (for instance, ROIs labeling cell
          nuceli) versus a comparison ROI (for instance, pixels not
          labeled as cells)

    getMeanGrayLevel(ROI,img)

        - Get the average gray level within an ROI on an image

    getLabelsAndLocations(ROIs,img,xForm2Center=True)

        - Organize ROI names and x/y coordinates into a python
          dictionary

    getDC_JI(seg1,seg2)

        - Computes the dice coefficient and jaccard index comparing two
          segmentations

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Store a constant variable with the amount of pixel wiggle room we're
# controlling when we grow and shrink ROIs to ensure complete overlap
wiggleRoom = 10

# Import our ImageProcessing module so we can make max projections
from ImageTools import ImageProcessing

# Import IJ so we can run macros commands and ImagePlus so we can make
# ImagePlus objects
from ij import IJ, ImagePlus

# Import Fiji's Rois
from ij.gui import Roi, PointRoi, ShapeRoi

# Import ImageJ's ROI rotator so we can rotate field of view ROIs, and
# ROI enlarger so we can grow and shrink ROIs
from ij.plugin import RoiRotator, RoiEnlarger
roirotator = RoiRotator()
roienlarger = RoiEnlarger()

# Import floor and ceil from math so we can round up and down
from math import floor, ceil

# Import ImageJ's threshold to selection filter
from ij.plugin.filter import ThresholdToSelection
thresholdtoselection = ThresholdToSelection()

# Import os so we can get the parent directory of a file, check to see
# if directories exist, and create directories
import os

# Import Fiji's ROI Manager
from ij.plugin.frame import RoiManager

# Create an instance of the RoiManager class silently
RM = RoiManager()

# Activate RoiManager object
rm = RM.getRoiManager()

# Import izip so we can iterate across multiple lists
from itertools import izip

# Import our statistics tools
import Stats

########################################################################
############################# gridOfFields #############################
########################################################################

# Define a class of objects to divide up an image into a grid-like set
# of fields of view
class gridOfFields:
    '''
    Class of objects that will divide up an image into a grid-like set
    of fields of view, where each field overlaps into its neighbors by a
    given amount. Stores the following attributes:

        * ROIs (list of Fiji ROIs): A list of square ROIs
          corresponding to separate fields of view sampled in a
          grid-like manner across an image. These ROIs will be twice
          the size of field_size and overlap 50% into the
          neighboring fields of view.

        * rotation (float): Amount that the field of views are rotated
                            from the horizontal in degrees

        * fieldBoundary (Fiji ROI): ROI with the size and rotation of a
                                    true field of view with no overlap

    gridOfFields(img,field_size,field_overlap,isRotated)

        - img (ImagePlus): Image that you want to divide into fields of
                           view

        - field_size (int): Size of the fields of view you want to
                            divide up your image into

        - field_overlap (int): Amount of overlap you want to exist
                               between neighboring fields of view

        - rotation (float): How much the tile scan was rotated during
                            image preprocessing

    AR Oct 2021
    AR Jan 2022: Rewrote to account for rotated tile scans
    AR Feb 2022: Changed the rotation of the fields of view to account
                 for the potential that the image was rotated 180
                 degrees, delete variables and close images after use
    AR Feb 2023: Don't need to normalize the z-stack, just the max projection
    '''

    # Define initialization function to create new instances of this
    # class of objects
    def __init__(self,img,field_size,field_overlap,rotation):

        # Store the rotation as an attributes of the object
        self.rotation = rotation % -90 # The rotation needs to be
                                       # transformed to make sure it's
                                       # divisible by 90 and the sign
                                       # needs to be flipped

        # Generate a maximum intensity projection of the input image
        imgStack = ImageProcessing.zStack(img)
        maxProj = imgStack.maxProj()
        del imgStack

        # Normalize the pixel intensities of the max projection
        maxProj = ImageProcessing.normalizeImg(maxProj)

        '''
        # Normalize the image so that the pixel intensities are brighter
        normalizedImg = ImageProcessing.normalizeImg(img)

        # Create a z-stack object for this image
        imgStack = ImageProcessing.zStack(normalizedImg)
        normalizedImg.close()
        del normalizedImg

        # Generate a maximum intensity projection of the image
        maxProj = imgStack.maxProj()
        imgStack.orig_z_stack.close()
        del imgStack
        '''

        # Create an ROI surrounding just the area of the tile scan that
        # we want to sample from, using the max projection
        self.imgROI = selectNonBlackRegion(maxProj)

        # Clear the max projection
        maxProj.close()
        del maxProj

        # Use the image ROI and the size of the original image to create
        # an image segmentation mask, labeling the full area we need to
        # sample from. We'll use this segmentation mask to keep track of
        # what has already been sampled, and what hasn't.
        img.setRoi(self.imgROI)
        self.imgSegMask = ImagePlus('Area2Sample',img.createRoiMask())
        self.imgSegMask.show()

        # Store the total width of a full field of view
        fullFieldWidth = field_size + (2 * field_overlap)

        # Store the width of a field and one overlap region
        fieldPlusOverlap = field_size + field_overlap

        # Store the total area of the field of view
        fieldArea = (fullFieldWidth) ** 2

        # Start a list of all fields of view that we want to measure
        # from
        self.ROIs = []

        # Store the approximate area of the image ROI
        imgROIArea = self.imgROI.getFloatWidth() * self.imgROI.getFloatHeight()

        # Store a counter for all fields of view
        iFov = 1

        # We're going to gradually shrink the ROI overtime. Check to see
        # if the area of the ROI is larger than our field of view size
        while imgROIArea > fieldArea:

            # Get the top left point of the current imgROI
            topLPt = getTopLeftPoint(self.imgROI)

            # Make a full sized field of view at this top left point
            newField = makeRotatedR0I(topLPt,fullFieldWidth,self.rotation)

            # Check to see if this field of view is fully contained
            # within the image ROI
            if isContained(newField,self.imgROI):

                # Rename the field of view, keeping track of its number
                newField.setName('Field-{}'.format(iFov))

                # Increase the field number
                iFov += 1

                # Store this field of view in our list of fields
                self.ROIs.append(newField)

                # Crop the full field from the image
                self.cropNewField(topLPt,fieldPlusOverlap)

            # If the field was not contained ...
            else:

                # Only crop out a square area with a width of two field
                # overlaps
                self.cropNewField(topLPt,field_overlap)

            # Update the approximate area of the region remaining to be
            # divided up
            imgROIArea = self.imgROI.getFloatWidth() * self.imgROI.getFloatHeight()

        # Close and clear the segmentation mask and image left to sample
        # ROI
        self.imgSegMask.close()
        delattr(self,'imgSegMask')
        delattr(self,'imgROI')

        # Each of these fields of view will later be cropped. Find the
        # central coordinate of this crop
        fovCenter = (self.ROIs[0].getFloatWidth() / 2.0,
                     self.ROIs[0].getFloatHeight() / 2.0)

        # Create an ROI centered at the center of the field of view with
        # the true field of view size (no overlap)
        halfFieldSize = float(field_size) / 2.0
        baseFovBoundsROI = Roi(fovCenter[0] - halfFieldSize,
                               fovCenter[1] - halfFieldSize,
                               field_size,field_size)

        # Rotate this field of view to generate our final true field
        # boundary
        self.fieldBoundary = roirotator.rotate(baseFovBoundsROI,
                                               self.rotation,
                                               fovCenter[0],
                                               fovCenter[1])

    # Define a method that will clear the non-overlapping portion of the
    # field of view from the max projection to keep track of where we
    # have already sampled from
    def cropNewField(self,topLeftPoint,cropWidth):

        # Make a field of view that is missing both overlapping
        # regions, this will be used to crop the area from the max
        # projection to keep track of what areas of the image have
        # already been sampled
        field4Cropping = makeRotatedR0I(topLeftPoint,ceil(cropWidth/2.0),
                                        self.rotation)

        # Sometimes the image ROI will have fuzzy edges, so it's hard to
        # have ROIs fit perfectly within the area that was actually
        # imaged at the microscope. Given this, we're going to enlarge
        # the region to remove by the amount of overlap we want to see
        # between the fields to give us more wiggle room.
        enlargedField2Crop = roienlarger.enlarge(field4Cropping,
                                                 floor(cropWidth/2.0))

        # Make sure the segmentation is displayed and add our field to
        # it
        self.imgSegMask.show()
        self.imgSegMask.setRoi(enlargedField2Crop)

        # Enlarging the ROI will change its type, change it back to a
        # rectangle
        IJ.run('Fit Rectangle')

        # Clear the image contained within the ROI we're using for
        # cropping, this way we know that we already sampled from this
        # region
        self.imgSegMask.cut()

        # Remove the ROI from the max projection
        self.imgSegMask.deleteRoi()

        # Convert the image segmentation to an roi to update our image
        # selection
        self.imgROI = ImageProcessing.segmentation2ROIs(self.imgSegMask)

        # Check to see if a list of ROIs was returned by the previous
        # command
        if isinstance(self.imgROI,(list,tuple)):

            # Combine all of the ROIs in img ROI
            self.imgROI = combineROIs(self.imgROI)

########################################################################
######################### selectNonBlackRegion #########################
########################################################################

# Define a function to select just the relevant portion of the image
# that isn't all black
def selectNonBlackRegion(img,cleanUpSelection=True):
    '''
    Makes an ROI just around the non-black region of the image

    selectNonBlackRegion(img)

        - img (Fiji ImagePlus): Image you want to process

        - cleanUpSelection (Boolean): Flag governing whether you want
                                      to clean up the selection after
                                      thresholding

    OUTPUT Fiji ROI selecting the non-black region of the image

    AR Jan 2022
    AR May 2022 Make sure that ROI is not polygon before cleaning it up
    AR July 2022 Make sure that ROI is a composite selection before clean up
    '''

    # Get the statistics for the image so we can know the min and max
    # pixel value
    imgStats = img.getStatistics()

    # Set a threshold selecting all pixels that are greater than the
    # smallest possible pixel value
    IJ.setRawThreshold(img,imgStats.min+1,imgStats.max,None)
    del imgStats

    # Display the image
    img.show()

    # Convert the threshold to an ROI
    nonBlackROI = thresholdtoselection.convert(img.getProcessor())

    # Display the ROI on the image
    img.setRoi(nonBlackROI)

    # Fill any holes in the ROI
    IJ.run("Fill ROI holes", "")

    # Check to see if we want to clean up the ROI
    if cleanUpSelection and nonBlackROI.getTypeAsString() == 'Composite':

        # Clean up the ROI and return
        return cleanUpROI(nonBlackROI,img)

    # Otherwise ...
    else:

        # Just return the raw selection after closing the original image
        img.hide()
        return nonBlackROI

########################################################################
############################## cleanUpROI ##############################
########################################################################

# Define a function that will clean up any loose edges of an ROI
def cleanUpROI(ROI,img):
    '''
    Removes loose overhangs from ROIs

    cleanUpROI(ROI)

        - ROI (Fiji ROI): Selection you want to clean up

        - img (Fiji ImagePlus): Image containing your selection

    OUTPUT Fiji ROI with the cleaner version of the original ROI

    AR Jan 2022
    '''

    # Store all currently open ROIs in the ROI manager before clearing
    prevOpenROIs = getOpenROIs()
    clearROIs()

    # Add the ROI to the ROI Manager
    addROIs2Manager(ROI)

    # Make sure that the image is displayed with the ROI
    img.show()
    img.setRoi(ROI)

    # Instruct the ROI Manager to split up the ROI into separate
    # components. If there are areas to be cleaned up, these will be
    # divided off the main region of interest
    rm.runCommand('Split')

    # Grab all of the ROIs from the ROI manager, aside from the ROI we
    # added at the beginning, which would be the first one in the list
    splitROIs = getOpenROIs()[1:]

    # For each split up ROI, estimate the area of the ROI
    splitROIAreas = [ROI.getFloatWidth() * ROI.getFloatHeight() for ROI in splitROIs]

    # The cleaned up ROI will be the split ROI with the largest area
    cleanedUpROI = splitROIs[splitROIAreas.index(max(splitROIAreas))]

    # Restore the ROI Manager back to the original state
    clearROIs()
    addROIs2Manager(prevOpenROIs)

    # Remove the ROI from the image and close it
    img.deleteRoi()
    img.hide()

    # Return the final cleaned up ROI
    return cleanedUpROI

########################################################################
############################ makeRotatedR0I ############################
########################################################################

# Define a function to make rotated ROIs
def makeRotatedR0I(topLeftPoint,width,rotation):
    '''
    Makes rotated ROIs

    makeRotatedR0I(topLeftPoint,width,rotation)

        - topLeftPoint (Tuple of 2 Floats): x and y coordinates of the
                                            top left point of your final
                                            rotated ROI

        - width (float): The desired width of your ROI

        - rotation (float): The desired rotation of your ROI in degrees

    OUTPUT Fiji ROI containing rotated square selection

    AR Jan 2022
    '''

    # Make a base ROI that's located at the correct x and y coordinates
    # and has the correct width
    baseROI = Roi(topLeftPoint[0],topLeftPoint[1],width,width)

    # Rotate the field of view according to the angle of rotation and
    # the top left point around which you want to rotate
    return roirotator.rotate(baseROI,rotation,topLeftPoint[0],
                             topLeftPoint[1])

########################################################################
############################ getTopLeftPoint ###########################
########################################################################

# Define a method that will identify the point with the lowest x-pixel
# value within an ROI
def getTopLeftPoint(ROI):
    '''
    Returns the top left point of an ROI

    getTopLeftPoint(ROI)

        - ROI (Fiji ROI): Region you want the top left point of

    OUTPUTS Tuple of floats represent the x and y coordinate of the top
            left point of the region

    AR Jan 2022
    '''

    # Convert the ROI into a float polygon
    floatPoly = ROI.getFloatPolygon()

    # Store all of the x and y values of this float polygon
    xPoints = floatPoly.xpoints
    yPoints = floatPoly.ypoints
    del floatPoly

    # Store the minimum x value in the float polygon
    topLeftXVal = min(xPoints)

    # Get all point indicies with the smallest x value
    smallXIndicies = [i for i, x in enumerate(xPoints) if x == topLeftXVal]
    del xPoints

    # Identify the minimum y value of all indicies with the minimum
    # x-value
    topLeftYVal = min([yPoints[i] for i in smallXIndicies])
    del yPoints, smallXIndicies

    # Return this top left point as a tuple, nudging it by a pixel
    return (topLeftXVal,topLeftYVal)

########################################################################
############################## isContained #############################
########################################################################

# Define a function to check to see if one ROI is contained within
# another
def isContained(containedROI,containingROI):
    '''
    Check to see if one region is contained within another

    isContained(containedROI,containingROI)

        - containedROI (Fiji ROI): Region that might be contained within
                                   the larger ROI

        - containingROI (Fiji ROI): Region that might contain the
                                    smaller ROI

    OUTPUT True if containedROI is inside containingROI, otherwise False

    AR Jan 2022
    '''

    # Compute the intersection between the two ROIs
    ROIUnion = getIntersectingROI([containedROI,containingROI])

    # Estimate the area of both the union and the smaller region that
    # might be contained
    ROIUnionArea = ROIUnion.getFloatWidth() * ROIUnion.getFloatHeight()
    containedROIArea = containedROI.getFloatWidth() * containedROI.getFloatHeight()

    # If there is a 1% or less difference in the estimated areas, we'll
    # predict that the region in question was contained in the larger
    # area
    return (abs(ROIUnionArea - containedROIArea) / containedROIArea) < 0.01

########################################################################
############################## subtractROI #############################
########################################################################

# Define a function to crop out a specified region from an ROI
def subtractROI(TotalRegion,Region2Remove,img,growth=0):
    '''
    Function that will subtract one ROI from another

    subtractROI(TotalRegion,Region2Remove)

        - TotalRegion (Fiji ROI): Region that you want to subtract from

        - Region2Remove (Fiji ROI): Portion of TotalRegion that you want
                                    to remove

        - img (Fiji ImagePlus): An image containing your regions of
                                interest

        - growth (int): How much do you want to expand your
                        Region2Remove before subtracting from Total
                        Region (default = 0, no growth)

    OUTPUT Fiji ROI storing the cropped region of interest

    AR Jan 2022
    '''

    # Make sure that the image is displayed
    img.show()

    # Sometimes ROIs will have fuzzy edges, so it's hard to have ROIs
    # overlap exactly. Given this, we're going to enlarge the region
    # to remove by 2 pixels to give us wiggle room.
    EnlargedRegion2Remove = roienlarger.enlarge(Region2Remove,growth)

    # Add this enlarged region to remove to our displayed image
    img.setRoi(EnlargedRegion2Remove)

    # Fit this new ROI to a rectangle
    IJ.run('Fit Rectangle')

    # Grab the edited ROI
    EnlargedRectangularRegion2Remove = img.getRoi()

    # Compute the area where the enlarged region and the total region
    # overlap
    FinalRegion2Remove = getIntersectingROI([EnlargedRectangularRegion2Remove,
                                             TotalRegion])
    del EnlargedRegion2Remove

    # Generate shape ROIs for both the total region and the final region
    # to remove
    sFinalRegion2Remove = ShapeRoi(FinalRegion2Remove)
    sTotalRegion = ShapeRoi(TotalRegion)
    del FinalRegion2Remove

    # Perform a unary exclusive or operation to subtract the final
    # region to remove from the total region
    croppedROI = sTotalRegion.xor(sFinalRegion2Remove)

    # Sometimes after cropping, a small stray piece will be left off.
    # Let's clean up the ROI if necessary before returning the final ROI
    croppedCleanedROI = cleanUpROI(croppedROI,img)

    # Remove the ROI from the image and close it
    img.deleteRoi()
    img.hide()

    # Return the final ROI
    return croppedCleanedROI

########################################################################
########################## getIntersectingROI ##########################
########################################################################

# Define a function to get the union of a list of ROIs
def getIntersectingROI(ROIs):
    '''
    Function that will return the intersection of a list of ROIs

    getIntersectingROI(ROIs)

        - ROIs (List of Fiji ROIs): ROIs for which you want to find the
                                    overlap

    OUTPUT Fiji ROI representing the region where all inputted ROIs
    intersect

    AR Jan 2022
    '''

    # Create a shape ROI for the first ROI in our list
    union = ShapeRoi(ROIs[0])

    # Loop across all other ROIs
    for ROI in ROIs[1:]:

        # Create a Shape ROI for this ROI
        sROI = ShapeRoi(ROI)

        # Update the union of this ROI with our current selection
        union = sROI.and(union)

    # Return the final union of all ROIs in the list
    return union

########################################################################
############################# getImgInROI #############################
########################################################################

# Define a function that will return the portion of an image contained
# within an ROI
def getImgInROI(img,ROI):
    '''
    Function that will return the portion of an image contained within
    an ROI

    getImgInROI(img,ROI)

        - img (Fiji ImagePlus): Image to be cropped from

        - ROI (Fiji ROI): ROI defining the area to crop from img

    OUTPUT

        - cropped_img (Fiji ImagePlus): Area of img contained within ROI

    AR Oct 2021
    '''

    # Overlay the ROI on top of the image
    img.setRoi(ROI)

    # Return a copy of the image within the ROI
    croppedImg = img.crop('stack')

    # Reset the name of this newly cropped image, combining the names of
    # the ROI and the img
    croppedImg.setTitle(ROI.getName() + '_' + img.getTitle())

    # Return final image
    return croppedImg

########################################################################
############################## getOpenROIs #############################
########################################################################

# Define a function to get all ROIs open in the ROI Manager
def getOpenROIs():
    '''
    Function that will return all ROIs in the ROI Manager

    getOpenROIs()

    OUTPUT Fiji ROI Object if only one ROI was in the ROI Manager, list
           of ROIs if multiple ROIs were in the ROI Manager, or None if
           there were no ROI objects

    AR Oct 2021
    '''

    # Get a list of all ROIs from the ROI Manager
    ROIs = rm.getRoisAsArray()

    # Check to see if only one ROI was present
    if len(ROIs) == 1:

        # If there was only one ROI, just return that ROI as an ROI
        # object rather than a list of one ROI
        return ROIs[0]

    # If there weren't any ROIs...
    elif len(ROIs) == 0:

        # ... return None
        return None

    # If multiple ROIs were present, return as a list rather than a java
    # array
    return list(ROIs)

########################################################################
############################ addROIs2Manager ###########################
########################################################################

# Define a function to load ROI objects to the Fiji ROI Manager
def addROIs2Manager(ROIs):
    '''
    Function that will add Fiji ROIs to the Fiji ROI Manager

    addROIs2Manager(ROIs)

        - ROIs (List of Fiji ROIs or Singular Fiji ROI): ROI(s) you want
                                                         to add to ROI
                                                         Manager

    AR Oct 2021
    '''

    # Check to see if a list of ROIs were provided
    if isinstance(ROIs,(tuple,list)):

        # Add each ROI in the list individually to the ROI Manager
        [rm.addRoi(ROI) for ROI in ROIs]

    # If only one ROI was specified...
    else:

        # Add this ROI to the ROI Manager
        rm.addRoi(ROIs)

########################################################################
############################### saveROIs ###############################
########################################################################

# Define a function that can be used to save Fiji ROIs to files
def saveROIs(ROIs,outFilePath):
    '''
    Function that will save either singular or sets of ROIs to a file

    saveROIs(ROIs,outFilePath)

        - ROIs (Singular Fiji ROI or List of ROIs): ROI(s) to save

        - outFilePath (String): Path to the file where you would like to
                                save. If the parent directory doesn't
                                exist for this file, it will be created.

    AR Oct 2021
    '''

    # Get the directory we will be saving the ROIs to
    outDir = os.path.dirname(outFilePath)

    # Check to see if this directory already exists
    if not os.path.exists(outDir):

        # Create the directory we will be saving to if necessary
        os.makedirs(outDir)

    del outDir

    # Store all of the ROIs currently in the ROI Manager so we can load
    # them back later
    openROIs = getOpenROIs()

    # Remove all ROIs from the ROI Manager
    clearROIs()

    # Add the ROI(s) to the ROI Manager
    addROIs2Manager(ROIs)

    # Save the ROI(s) to the file the user specified
    rm.runCommand('Save',outFilePath)

    # Clear the ROI manager
    clearROIs()

    # Check to see if there were ROIs in the ROI Manager before this
    # function was called
    if openROIs is not None:

        # Return the ROI Manager back to its original state by loading
        # back the ROIs
        addROIs2Manager(openROIs)

########################################################################
############################# openROIFile ##############################
########################################################################

# Define a function to open ROI files
def openROIFile(ROIFile):
    '''
    Function that will open and ROI File and return all ROIs that were
    saved

    openROIFile(ROIFile)

        - ROIFile (String): Path to file containing ROIs you want to
                            open

    OUTPUT List of Fiji ROI objects or a singular ROI object that was
           saved in your ROI File

    AR Oct 2021
    '''

    # Store all currently open ROI objects in the ROI Manager so we can
    # re-load them after opening the file
    openROIs = getOpenROIs()

    # Remove all ROIs from the ROI Manager
    clearROIs()

    # Read the ROI file and open all saved ROIs into the ROI Manager
    rm.runCommand('Open',ROIFile)

    # Get all of the ROIs we just opened
    ROIsFromFile = getOpenROIs()

    # Remove all ROIs from ROI Manager
    clearROIs()

    # Re-load all ROIs that were open before running the function
    if openROIs is not None:
        addROIs2Manager(openROIs)

    # Return the ROIs we opened from the file
    return ROIsFromFile

########################################################################
############################### clearROIs ##############################
########################################################################

# Define a function to clear ROIs from the ROI Manager
def clearROIs():
    '''
    Function that clears all of the ROIs in the ROI Manager

    clearROIs()

    AR Nov 2021
    '''

    # Clear all ROIs from the ROI Manager
    rm.reset()

########################################################################
############################## ROIsInArea ##############################
########################################################################

# Define a function that will check which ROIs are within a given area
# of an image
def ROIsInArea(ROIs2Check,AreaContainingROIs):
    '''
    Function that will check whether each ROI in a list of ROIs is
    contained within a given area of an image

    ROIsInArea(ROIs2Check,AreaContainingROIs)

        - ROIs2Check (List of Fiji ROIs): ROIs that you want to test to
                                          if they are contained within
                                          a given area of an image

        - AreaContainingROIs (Fiji ROI): The area within which you want
                                         ROIs to reside

    OUTPUT List of all Fiji ROIs whose rotational center resides within
           the area provided by the user

    AR Nov 2021
    '''

    # Check to see whether each ROI's center is contained within the specified
    # area
    isContained = [AreaContainingROIs.contains(int(round(ROI.getRotationCenter().xpoints[0])),
                                               int(round(ROI.getRotationCenter().ypoints[0]))) for ROI in ROIs2Check]

    # Return a list of all ROIs whose centers were contained within the
    # desired area
    return [ROIs2Check[i] for i in range(len(ROIs2Check)) if isContained[i]]

########################################################################
############################## getROIArea ##############################
########################################################################

# Define a function that will get the area of an ROI in physical units
def getROIArea(ROI,img):
    '''
    Function that will compute the area of an ROI in physical units
    (e.g., microns) instead of just pixel units

    getROIArea(ROI,img)

        - ROI (Fiji ROI): ROI that you want the area of

        - img (Fiji ImagePlus): Image on which the ROI would be
                                superimposed

    getROIArea(ROI,imgCal)

        - ROI (Fiji ROI): ROI that you want the area of

        - imgCal (Fiji Image Calibration): Calibration of the image
                                           on which the ROI would be
                                           superimposed

    OUTPUT list of two outputs. The first a float containing the area of
    the ROI. The second, the unit of the area (e.g. microns squared).

    AR Nov 2021
    AR Jun 2023 Correcting output as the previous code only worked for
                rectangular ROIs that were not rotated
    '''

    # If we are importing an image rather than an image calibration
    if isinstance(img,ImagePlus):

        # Store the image calibration set for the image. This will contain
        # information about the pixel to physical unit conversion.
        imgCal = img.getCalibration()

    # If our input was an image calibration
    else:
        imgCal = img

    # Compute the statistics for this ROI
    ROIStats = ROI.getStatistics()

    # Use the image calibration as well as the size of our ROI to
    # compute the area of the ROI.
    area = ROIStats.area * imgCal.getX(1)**2#imgCal.getX(ROI.getFloatWidth()) * imgCal.getY(ROI.getFloatHeight())

    # Get the physical units of the area of the image. Needed to add a
    # squared at the end of the string.
    units = imgCal.getUnit() + '_Squared'

    # Check to see if the micron symbol was used in the unit
    # specification
    if u'\xb5' in units:

        # Convert the micron symbol to a u
        units = units.replace(u'\xb5','u')

    # Return the area and the units
    return [area, units]

########################################################################
############################## combineROIs #############################
########################################################################

# Define a function to combine ROIs
def combineROIs(ROIs):
    '''
    Function that will combine a set of ROIs into a single composite

    combineROIs(ROIs)

        - ROIs (List of Fiji ROIs): ROIs that you want to combine

    OUTPUT Fiji ROI that is the composite of the ROIs you inputted

    AR Nov 2021
    AR Feb 2022 Check to see if only one ROI is listed to be combined
    '''

    # Initialize a shape ROI that will store the combined ROI using the
    # first ROI in your list
    combinedROI = ShapeRoi(ROIs[0])

    # Check to make sure more than one ROI is present in the list
    if len(ROIs) > 1:

        # Loop across all other ROIs in the list
        for ROI in ROIs[1:]:

            # Convert this ROI into a shape ROI
            shapeROI = ShapeRoi(ROI)

            # Add the new shape ROI to our combined ROI
            combinedROI = combinedROI.or(shapeROI)

    # Return the final combined ROI
    return combinedROI

########################################################################
########################### getBackgroundROI ###########################
########################################################################

# Define a function to get an ROI labeling all pixels in background of
# field of view
def getBackgroundROI(nucROIs,fieldROI,refImg):
    '''
    Function that will compute an ROI representing all pixels that were
    not segmented as part of nuclei

    getBackgroundROI(nucROIs,fieldROI,refImg)

        - nucROIs (List of Fiji ROIs): All ROIs labeling cells within a
                                       field of view.

        - fieldROI (Fiji ROI): ROI marking the true boundary of the
                               field of view

        - refImg (Fiji ImagePlus): Image with the same dimensions as the
                                   full field of view (with overlap) to
                                   serve as a reference

    OUTPUT Fiji ROI that labels all pixels that were not contained
    within cell nuclei in the field of view

    AR Nov 2021
    '''

    # Combine all of the nuclear ROIs into a single composite ROI
    nucROI = combineROIs(nucROIs)

    # Invert this combined ROI so that it labels all pixels not
    # associated with cell nuclei
    notNucROI = ShapeRoi(nucROI.getInverse(refImg))

    # Crop this ROI so that it only labels pixels that are within the
    # true field of view boundaries. Return this final ROI.
    return notNucROI.and(ShapeRoi(fieldROI))

########################################################################
############################## computeSNR ##############################
########################################################################

# Define a function to compute SNR
def computeSNR(ROI,backgroundROI,img):
    '''
    Function that will compute the signal to noise ratio (SNR) of the
    gray level inside a signal ROI compared to a background ROI

    computeSNR(ROI,backgroundROI,img)

        - ROI (Fiji ROI): Areas in the image where your signal is
                          located (e.g. a stained cell)

        - backgroundROI (Fiji ROI): Area in image where there is
                                    background (e.g. where there are no
                                    cells)

        - img (Fiji ImagePlus): Image from which to measure gray level

    OUTPUT float representing your SNR

    AR Nov 2021
    AR Feb 2022 Edited SNR formula and changed from list of signal ROIs
                to single composite signal ROI
    '''

    # Superimpose the background ROI on the image
    img.setRoi(backgroundROI)

    # Store the statistics for the background of this image
    imgStats = img.getStatistics()

    # Store the mean and standard deviation of the background
    avgNoise = imgStats.mean
    stdNoise = imgStats.stdDev

    # Superimpose the ROI containing the signal on our image
    img.setRoi(ROI)

    # Compute and return the final SNR
    return (img.getStatistics().mean - avgNoise) / stdNoise

########################################################################
############################ grayLevelTTest ############################
########################################################################

# Write a function to compute the t statistic and accompanying p value
# comparing the gray level inside and outside of an ROI
def grayLevelTTest(ROIs,ROI2Compare,img):
    '''
    Function that will compute the t-statistic comparing the gray level
    inside each ROI (for instance, ROIs labeling cell nuceli) versus a
    comparison ROI (for instance, pixels not labeled as cells)

    grayLevelTTest(ROIs,ROI2Compare,img)

        - ROIs (List of Fiji ROIs): Areas in the image you want to test
                                    to see if they have a greater pixel
                                    intensity

        - ROI2Compare (Fiji ROI): Area in image you want to compare the
                                  gray level of each of your ROIs to

        - img (Fiji ImagePlus): Image from which to measure gray level

    OUTPUT lists of floats representing the t value of each one-sided
    t-test seeing if each ROI has a higher gray level than the
    comparison ROI

    AR Nov 2021
    AR Mar 2022 Make sure ROIs are removed from image at end of function
    '''

    # Superimpose the comparison ROI on top of the image
    img.setRoi(ROI2Compare)

    # Get the statistics on the gray levels within this comparison ROI
    compareStats = img.getStatistics()

    # Start a list with all the t-statistics we will return
    testResults = []

    # Loop across all ROIs
    for ROI in ROIs:

        # Superimpose this ROI on the image
        img.setRoi(ROI)

        # Get the statistics of the gray levels within this ROI
        ROIStats = img.getStatistics()

        # Get the t-statistic for the test with a null hypothesis that
        # this ROI has a higher gray level than the comparison. Does not
        # assume equal variance.
        testResults.append(Stats.ttest(ROIStats.mean,compareStats.mean,
                                       ROIStats.stdDev**2,
                                       compareStats.stdDev**2,
                                       ROIStats.pixelCount,
                                       compareStats.pixelCount))

    # Delete the ROI from the image
    img.deleteRoi()

    # Return all of our test results
    return testResults

########################################################################
########################### getMeanGrayLevel ###########################
########################################################################

# Define a function to get the average pixel intensity inside of an ROI
def getMeanGrayLevel(ROI,img):
    '''
    Get the average gray level within an ROI on an image

    getMeanGrayLevel(ROI,img)

        ROI (ImageJ ROI): The ROI that you want the mean pixel intensity
                          of

        img (ImagePlus): Image containing your ROI

    OUTPUT average pixel intensity inside the ROI as a float

    AR Feb 2022
    '''

    # Place the ROI on the image
    img.setRoi(ROI)

    # Return the average pixel intensity inside the ROI
    return img.getStatistics().mean

########################################################################
######################### getLabelsAndLocations ########################
########################################################################

# Write a function to get the names and locations of a set of ROIs
def getLabelsAndLocations(ROIs,img,xForm2Center=True):
    '''
    Organize ROI names and x/y coordinates into a python dictionary

    getLabelsAndLocations(ROIs,img,xForm2Center=True)

        - ROIs (List of ImageJ ROIs): ROIs you want the labels and
                                      coordinates of

        - img (ImagePlus): Image containing your ROIs

        - xForm2Center (Boolean): Do you want to transform the data
                                  points so that (0,0) is at the center
                                  of the image? Default sets (0,0) as
                                  center

    OUTPUT dictionary with keys a python dictionary with keys
    'Cell_Type','X_Coordinate_In_{}' and 'Y_Coordinate_In_{}' where {}
    is replaced with the length unit in the image (e.g. microns). Each
    of these keys stores lists of the same length as your list of ROIs
    with the names of the ROIs and the x and y coordinates of the ROIs,
    respectively.

    AR Feb 2022
    AR June 2023 Use corrected getROIArea function 
    '''

    # Get the calibration for this image
    imgCal = img.getCalibration()

    # Store the units used in the image
    imgUnits = imgCal.getUnits()

    # Initialize python dictionary that will store the cell types,
    # locations and morphology metrics based on these ROIs
    ROIInfo = {'Cell_Type': [],
               'X_Coordinate_In_{}'.format(imgUnits): [],
               'Y_Coordinate_In_{}'.format(imgUnits): [],
               'Major_Diameter_In_{}'.format(imgUnits): [],
               'Minor_Diameter_In_{}'.format(imgUnits): [],
               'Area_In_{}_Squared'.format(imgUnits): [],
               'Perimeter_In_{}'.format(imgUnits): []}

    # If we want to set 0,0 to the center of the image
    if xForm2Center:

        # Identify the center of the image in pixels. We will set 0 as
        # this coordinate
        imgCenter = (float(img.getWidth())/2.0,float(img.getHeight())/2.0)

    # Otherwise
    else:

        # The center of the image will be at ImageJ's default 0,0
        imgCenter = (0.0,0.0)

    # Iterate across our list of ROIs
    for ROI in ROIs:

        # Make sure that the ROI is not associated with the image
        ROI.setImage(None)

        # Get the rotational center of this ROI
        ROICenter = ROI.getRotationCenter()

        # Get the x and y coordinate of the center of this ROI in
        # physical units and add to our dictionary
        ROIInfo['X_Coordinate_In_{}'.format(imgUnits)].append(imgCal.getX(ROICenter.xpoints[0] - imgCenter[0]))
        ROIInfo['Y_Coordinate_In_{}'.format(imgUnits)].append(imgCal.getY(ROICenter.ypoints[0] - imgCenter[1]))

        # Add the name of the ROI, which should store the cell type of
        # this selection
        ROIInfo['Cell_Type'].append(ROI.getName())

        # Store the length of the perimeter of the ROI
        ROIInfo['Perimeter_In_{}'.format(imgUnits)].append(imgCal.getX(ROI.getLength()))

        # Compute the area of the ROI
        ROIInfo['Area_In_{}_Squared'.format(imgUnits)].append(getROIArea(ROI,imgCal)[0])

        '''# Compute the statistics for this ROI
        ROIStats = ROI.getStatistics()

        # Compute the area of the ROI
        ROIInfo['Area_In_{}_Squared'.format(imgUnits)].append(ROIStats.area * imgCal.getX(1)**2)'''

        # Store the major and minor diameters of the ROI
        ROIInfo['Major_Diameter_In_{}'.format(imgUnits)].append(imgCal.getX(ROIStats.major))
        ROIInfo['Minor_Diameter_In_{}'.format(imgUnits)].append(imgCal.getX(ROIStats.minor))

    # Return the final python dictionary
    return ROIInfo

########################################################################
############################### getDC_JI ###############################
########################################################################

# Write a function to quantitatively compare segmentations
def getDC_JI(seg1,seg2,compareForeground=True,window2compare=None):
    '''
    Computes the dice coefficient and jaccard index comparing two
    segmentations

    getDC_JI(seg1,seg2)

        - seg1/seg2 (Image Plus): The two segmentation masks you want to
                                  quantitatively compare

    getDC_JI(seg1,seg2,compareForeground,window2compare)

        - compareBlankSpace (Boolean): Flag controlling whether you want
                                       to compare the foreground or
                                       background of the segmentation
                                       masks. (default = True, compare
                                       foreground)

        - window2compare (ROI): Area within the segmentations that you
                                want to compare

    OUTPUTS list of two floats representing the dice coefficient and the
            jaccard index, respectively, comparing these two
            segmentations

    AR April 2022
    AR Aug 2022 Adding logic for cases where a segmentation is blank
    '''

    # Make sure neither segmentation have any ROIs associated with them
    seg1.deleteRoi()
    seg2.deleteRoi()

    # Select the area of both segmentations that is not blank
    ROI1 = selectNonBlackRegion(seg1,False)
    ROI2 = selectNonBlackRegion(seg2,False)

    # Check to see if we want to compare the background of the
    # segmentations (i.e. the blank space in the image)
    if not compareForeground:

        # Invert these ROIs so that we are selecting all the area that
        # is blank. If ROI1 or ROI2 are None, the whole window to
        # compare is blank.
        try:
            totBlankROI1 = ROI1.getInverse(seg1)
        except:
            totBlankROI1 = window2compare
        try:
            totBlankROI2 = ROI2.getInverse(seg2)
        except:
            totBlankROI2 = window2compare

        # Shrink these ROIs so that they are contained within our window
        # of interest
        ROI1 = getIntersectingROI([totBlankROI1,window2compare])
        ROI2 = getIntersectingROI([totBlankROI2,window2compare])
        del totBlankROI1, totBlankROI2

    # If either of the segmentations are blank...
    if ROI1 is None or ROI2 is None:

        # ... then there is no intersection between the ROIs
        segIntersect = 0.0

        # If both segmentations are blank...
        if ROI1 is None and ROI2 is None:

            # ... the combination of ROI1 and ROI2 will also be blank
            segUnion = 0.0

            # and the total area segmented is zero
            totSegArea = 0.0

        # If just the first ROI is the blank one...
        elif ROI1 is None:

            # ... the combination of the ROIs is just the 2nd ROI
            segUnion = float(ROI2.getContainedFloatPoints().npoints)

            # and the total area segmented is the same as just the 2nd
            # ROI
            totSegArea = segUnion

        # Repeat the above for the condition where the 2nd ROI is blank
        else:

            segUnion = float(ROI1.getContainedFloatPoints().npoints)
            totSegArea = segUnion

    # otherwise...
    else:

        # Get the intersection between these two segmentations and
        # compute its size
        segIntersectROI = getIntersectingROI([ROI1,ROI2])
        segIntersect = float(segIntersectROI.getContainedFloatPoints().npoints)

        # Do the same for the union between these two segmentations
        segUnionROI = combineROIs([ROI1,ROI2])
        segUnion = float(segUnionROI.getContainedFloatPoints().npoints)

        # Get the total number of pixels across both segmentations
        totSegArea = float(ROI1.getContainedFloatPoints().npoints + ROI2.getContainedFloatPoints().npoints)

    # Compute the jaccard index, first checking to see if we would
    # divide by zero
    if segUnion > 0:

        JI = segIntersect/segUnion

    else:

        # If we have to divide by zero, report not a number
        JI = float('nan')

    # Do the same with the dice coefficient
    if totSegArea > 0:

        DC = (2.0 * segIntersect) / totSegArea

    else:

        DC = float('nan')

    # Return the final values
    return [DC,JI]
