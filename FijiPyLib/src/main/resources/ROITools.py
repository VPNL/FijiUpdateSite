'''
ROITools Module

This module contains tools to work easily with Fiji ROIs

    gridOfFields(img,field_size)

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
'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Import floor and ceil so we can round down
from math import floor

# Import Fiji's Rois
from ij.gui import Roi

# Import os so we can get the parent directory of a file, check to see
# if directories exist, and create directories
import os

# Import Fiji's ROI Manager
from ij.plugin.frame import RoiManager

# Create an instance of the RoiManager class silently
RM = RoiManager()

# Activate RoiManager object
rm = RM.getRoiManager()

########################################################################
############################# gridOfFields #############################
########################################################################

# Define a class of objects to divide up an image into a grid-like set
# of fields of view
class gridOfFields:
    '''
    Class of objects that will divide up an image into a grid-like set
    of fields of view, where each field overlaps 50% into its neighbors.
    Stores the following attributes:

        * ROIs (list of Fiji ROIs): A list of square ROIs
          corresponding to separate fields of view sampled in a
          grid-like manner across an image. These ROIs will be twice
          the size of field_size and overlap 50% into the
          neighboring fields of view.

        * fieldBoundary (Fiji ROI): Each ROI listed under the ROIs
          attribute overlaps 50% into its neighboring fields of
          view. When any of these fields are isolated, you can use
          this ROI to denote the true boundary of the field of view.

    gridOfFields(img,field_size)

        - img (ImagePlus): Image that you want to divide into fields of
                           view

        - field_size (int): Size of the fields of view you want to
                            divide up your image into

    AR Oct 2021
    '''

    # Define initialization function to create new instances of this
    # class of objects
    def __init__(self,img,field_size):

        # Get the dimensions of this image
        [w,h,_,_,_] = img.getDimensions()

        # Compute the number rows and columns of fields of view we can
        # divide the image into. Each field of view will have the size
        # field_size and then extend 50% into neighboring fields (total
        # size of 2*field_size). For the first and last field in a
        # given row or column, we need extra room for the field to
        # extend towards the edge of the image. We account for this by
        # calculating how many times the image width and height can be
        # divided into fields of field size, plus an extra field.
        nRows = int(floor(h/(field_size)) - 1)
        nCols = int(floor(w/(field_size)) - 1)

        # The first pixel to be included in the first field along each
        # row and column can be calculated by subtracting the middle of
        # the image (half the length of each image dimension) from half
        # the length of all fields of view spanning that dimension
        frst_pxl_in_frst_row = int((float(h)/2.0) - (float((nRows + 1) * field_size)/2.0)) + 1
        frst_pxl_in_frst_col = int((float(w)/2.0) - (float((nCols + 1) * field_size)/2.0)) + 1

        # Initialize a list that will store all of the field of view
        # ROIs
        fovs = []

        # Initialize a variable that will store the column number of the
        # field we are creating
        iRow = 1

        # Loop across all pixels defining the start of each row in the
        # grid of fields of view
        for start_pxl_in_row in range(frst_pxl_in_frst_row,h-(2*field_size),field_size):

            # Initialize a variable to store the row number of the field
            # we are creating
            iCol = 1

            # Loop across all pixels defining the start of each column
            # in the grid of fields of view
            for start_pxl_in_col in range(frst_pxl_in_frst_col,w-(2*field_size),field_size):

                # Make a square field of view ROI at this location
                fov = Roi(start_pxl_in_col,start_pxl_in_row,(2*field_size)-1,(2*field_size)-1)

                # Set the name of this field of view to include the row
                # and column number
                fov.setName('Row' + str(iRow) + '-Col' + str(iCol))

                # Add this field of view to our list of field of views
                fovs.append(fov)

                # Increase the column number
                iCol = iCol + 1

            # Increase the row number
            iRow = iRow + 1

        # Store our newly created list of fields of view as an object
        # attribute
        self.ROIs = fovs

        # Create a final ROI that denotes the true boundaries of the
        # field of view that doesn't overlap into neighboring fields
        fieldBoundary = Roi(floor(field_size/2) + 1,floor(field_size/2) + 1,field_size-2,field_size-2)

        # Give this final ROI a name
        fieldBoundary.setName(str(field_size) + ' Pixel Field of View Boundary')

        # Store this ROI as an object attribute
        self.fieldBoundary = fieldBoundary

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
    rm.reset()

    # Add the ROI(s) to the ROI Manager
    addROIs2Manager(ROIs)

    # Save the ROI(s) to the file the user specified
    rm.runCommand('Save',outFilePath)

    # Clear the ROI manager
    rm.reset()

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
    rm.reset()

    # Read the ROI file and open all saved ROIs into the ROI Manager
    rm.runCommand('Open',ROIFile)

    # Get all of the ROIs we just opened
    ROIsFromFile = getOpenROIs()

    # Remove all ROIs from ROI Manager
    rm.reset()

    # Re-load all ROIs that were open before running the function
    if openROIs is not None:
        addROIs2Manager(openROIs)

    # Return the ROIs we opened from the file
    return ROIsFromFile
