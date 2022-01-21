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
          the gray level inside a set of ROIs compared to the
          background

    grayLevelTTest(ROIs,ROI2Compare,img)

        - Function that will compute the t-statistic comparing the gray
          level inside each ROI (for instance, ROIs labeling cell
          nuceli) versus a comparison ROI (for instance, pixels not
          labeled as cells)

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Store a constant variable with the amount of pixel wiggle room we're
# controlling when we grow and shrink ROIs to ensure complete overlap
wiggleRoom = 10

# Import our ImageProcessing module so we can make max projections
from ImageTools import ImageProcessing

# Import IJ so we can run macros commands
from ij import IJ

# Import Fiji's Rois
from ij.gui import Roi, PointRoi, ShapeRoi

# Import ImageJ's ROI rotator so we can rotate field of view ROIs, and
# ROI enlarger so we can grow and shrink ROIs
from ij.plugin import RoiRotator, RoiEnlarger
roirotator = RoiRotator()
roienlarger = RoiEnlarger()

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
    of fields of view, where each field overlaps 50% into its neighbors.
    Stores the following attribute:

        * ROIs (list of Fiji ROIs): A list of square ROIs
          corresponding to separate fields of view sampled in a
          grid-like manner across an image. These ROIs will be twice
          the size of field_size and overlap 50% into the
          neighboring fields of view.

        * img (Fiji ImagePlus): The image that was divided up into
                                fields

        * maxProj (Fiji ImagePlus): The normalized maximum intensity
                                    projection of our image. Used to
                                    keep track of which portions of the
                                    image have already been sampled.

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
    '''

    # Define initialization function to create new instances of this
    # class of objects
    def __init__(self,img,field_size,field_overlap,rotation):

        # Store the image, field size, field overlap and degree of
        # rotation as attributes of the object
        self.img = img
        self.field_size = field_size
        self.field_overlap = field_overlap
        self.rotation = rotation

        # Check to see if the tile scan we're dividing up was rotated
        if rotation == 0:

            # We'll want to make sure the entire image is included
            imgROI = Roi(0,0,img.getWidth(),img.getHeight())

        # If the tile scan wasn't rotated...
        else:

            # If the image was rotated, we'll need to draw an ROI just
            # around the area that contains relevant data, avoiding
            # blank spaces around the edges
            imgROI = self.getRelevantRegion()

        # Store the total width of a full field of view
        fullFieldWidth = field_size + (2 * field_overlap)

        # Store the total area of the field of view
        fieldArea = (fullFieldWidth) ** 2

        # Start a list of all fields of view that we want to measure
        # from
        self.ROIs = []

        # Store the approximate area of the image ROI
        imgROIArea = imgROI.getFloatWidth() * imgROI.getFloatHeight()

        # We're going to gradually shrink the ROI overtime. Check to see
        # if the area of the ROI is larger than our field of view size
        while imgROIArea > fieldArea:

            # Get the top left point of the current imgROI
            topLPt = getTopLeftPoint(imgROI)

            # Make a full sized field of view at this top left point
            newField = makeRotatedR0I(topLPt,fullFieldWidth,rotation)

            # Check to see if this field of view is fully contained
            # within the image ROI
            if isContained(newField,imgROI):

                # Store this field of view in our list of fields
                self.ROIs.append(newField)

            # Crop our new field of view from our max projection so that
            # we can keep track of which areas of the image have already
            # been sampled
            self.cropNewField(topLPt)

            # Regenerate the ROI labeling the rest of the image that has
            # yet to be sampled from
            imgROI = self.getRelevantRegion()

            # Update the approximate area of the region remaining to be
            # divided up
            imgROIArea = imgROI.getFloatWidth() * imgROI.getFloatHeight()

        # Hide the max projection
        self.maxProj.hide()

    # Define a method that will clear the non-overlapping portion of the
    # field of view from the max projection to keep track of where we
    # have already sampled from
    def cropNewField(self,topLeftPoint):

        # Make a field of view that is missing both overlapping
        # regions, this will be used to crop the area from the max
        # projection to keep track of what areas of the image have
        # already been sampled
        field4Cropping = makeRotatedR0I(topLeftPoint,self.field_size,
                                        self.rotation)

        # Sometimes the image ROI will have fuzzy edges, so it's hard to
        # have ROIs fit perfectly within the area that was actually
        # imaged at the microscope. Given this, we're going to enlarge
        # the region to remove by the amount of overlap we want to see
        # between the fields to give us more wiggle room.
        enlargedField2Crop = roienlarger.enlarge(field4Cropping,
                                                 self.field_overlap)

        # Make sure the max projection is displayed and add our field to
        # it
        self.maxProj.show()
        self.maxProj.setRoi(enlargedField2Crop)

        # Enlarging the ROI will change its type, change it back to a
        # rectangle
        IJ.run('Fit Rectangle')

        # Clear the image contained within the ROI we're using for
        # cropping, this way we know that we already sampled from this
        # region
        self.maxProj.cut()

        # Remove the ROI from the max projection
        self.maxProj.deleteRoi()

    # Define a method that will produce an ROI just around the portion
    # of the image we care about
    def getRelevantRegion(self):

        # Check to see if we already have made a max intensity
        # projection of our image
        if not hasattr(self,'maxProj'):

            # Normalize the image so that the pixel intensities are brighter
            normalizedImg = ImageProcessing.normalizeImg(self.img)

            # Create a z-stack object for this image
            imgStack = ImageProcessing.zStack(normalizedImg)
            normalizedImg.close()
            del normalizedImg

            # Generate a maximum intensity projection of the image
            self.maxProj = imgStack.maxProj()
            imgStack.orig_z_stack.close()
            del imgStack

        # Display our maximum intensity projection
        self.maxProj.show()

        # Check to see if the dimensions of the image have already been
        # stored
        if not hasattr(self,'corners'):

            # Get the dimensions of the image
            height = self.maxProj.getHeight()
            width = self.maxProj.getWidth()

            # Store a list of the 4 corners of the image
            self.corners = [(wiggleRoom,wiggleRoom),
                            (wiggleRoom,height-1-wiggleRoom),
                            (width-1-wiggleRoom,wiggleRoom),
                            (width-1-wiggleRoom,height-1-wiggleRoom)]
            del height, width

        # Start a list that will store fuzzy select ROIs from the 4
        # corners of the image
        cornerROIs = []

        # Store all currently opened ROIs in the ROI Manager and then
        # clear
        prevOpenROIs = getOpenROIs()
        clearROIs()

        # Loop across the four corners of the image
        for (x,y) in self.corners:

            # Use the wand tool to fuzzy select the empty area at this
            # corner of the image
            IJ.doWand(x,y)

            # Add the newly drawn ROI to the ROI Manager
            rm.runCommand('Add')
        del x, y

        # Combine all of the ROIs into a composite
        _ = rm.runCommand('Combine')

        # Invert the combined ROI so that it selects the area we want to
        # sample from
        IJ.run('Make Inverse')

        # Smooth this ROI so that it's less fuzzy and more geometric
        IJ.run('Fit Spline')

        # Get the final ROI from the max projection
        smoothedRelevantROI = self.maxProj.getRoi()

        # Clear the ROI manager and restore it to its previous state
        clearROIs()
        addROIs2Manager(prevOpenROIs)

        # Return the final ROI
        return smoothedRelevantROI

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

    OUTPUT list of two outputs. The first a float containing the area of
    the ROI. The second, the unit of the area (e.g. microns squared).

    AR Nov 2021
    '''

    # Store the image calibration set for the image. This will contain
    # information about the pixel to physical unit conversion.
    imgCal = img.getCalibration()

    # Use the image calibration as well as the size of our ROI to
    # compute the area of the ROI.
    area = imgCal.getX(ROI.getFloatWidth()) * imgCal.getY(ROI.getFloatHeight())

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
    '''

    # Initialize a shape ROI that will store the combined ROI using the
    # first ROI in your list
    combinedROI = ShapeRoi(ROIs[0])

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
def computeSNR(ROIs,backgroundROI,img):
    '''
    Function that will compute the signal to noise ratio (SNR) of the
    gray level inside a set of ROIs compared to the background

    computeSNR(ROIs,backgroundROI,img)

        - ROIs (List of Fiji ROIs): Areas in the image where your signal
                                    is located (e.g. a stained cell)

        - backgroundROI (Fiji ROI): Area in image where there is
                                    background (e.g. where there are no
                                    cells)

        - img (Fiji ImagePlus): Image from which to measure gray level

    OUTPUT List of floats representing the SNR of each ROI in your
    inputted list of ROIs

    AR Nov 2021
    '''

    # Superimpose the background ROI on the image
    img.setRoi(backgroundROI)

    # Store the average gray level in the background of this image
    avgNoise = img.getStatistics().mean

    # Start a list that will store all of the SNR values for each ROI we
    # want to measure
    SNRs = []

    # Loop across all ROIs denoting areas of signal (e.g. cell nuclei)
    for ROI in ROIs:

        # Superimpose this ROI on our image
        img.setRoi(ROI)

        # Compute the signal inside this ROI and divide it by the noise
        SNRs.append(img.getStatistics().mean/avgNoise)

    # Return the list of SNRs of each ROI
    return SNRs

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

    # Return all of our test results
    return testResults
