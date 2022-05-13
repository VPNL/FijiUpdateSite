#@ File(label='Where are all of the cell labelings your researchers have completed?',style='directory') dataDir

'''
Compile Semi Auto Cell Labels

This script will compile all measurements and ROIs generated from our
semi-automated cell labeling pipeline. The user will specify the master
directory containing all of the semi-automated cell labelings that all
researchers conducted across the source image. Then, the script will
compile all measurements obtained from the individual csv files produced
for each field of view analyzed by the semi auto cell labeling plugin in
addition to all labeled ROIs. Outputs csv files containing all
measurements across fields of views and labeled cells. Also outputs .zip
files containing a set of ROIs representing the fields that were
analyzed as well as each nuclear segmentation colored and named by cell
type. These two ROI sets are meant to be displayed on the source image
these fields of view are gathered from.

AR April 2022
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so that we can ask the user the location of
# the orginal and re-done cell labelings
from java.io import File

# Convert the data directory from a Java File object to a string
cellLabelDir = dataDir.getAbsolutePath()

# Import our UIs module so we can make easy user interfaces
import UIs

# Import our image files module so we can locate files and directories
from ImageTools import ImageFiles

# Import regular expressions so we can search strings for patterns
import re

# Import os so we can join path elements
import os

# Import DataFiles module so we can work with csv files and python
# dictionaries
import DataFiles

# Import ImagePlus so we can open up images
from ij import ImagePlus
ImagePlus()

# Impor our ROI functions
import ROITools

# Import ROI so we can make field of view ROIs
from ij.gui import Roi

# Import the ROI Rotator plugin
from ij.plugin import RoiRotator
roirotator = RoiRotator()

# Import zip so we can sort a list based on another list
from itertools import izip

# Import colors so we can color ROIs
from java.awt import Color

########################################################################
####### GET INFORMATION ABOUT SOURCE IMAGE THESE FIELDS CAME FROM ######
########################################################################

# Create a list of all information we would like to collect for this set
# of fields of view
tileScanQs = ['Region_Imaged','Age_of_Sample','Sample_ID','Microscope_Slide']

# Ask the user for information about these fields of view
tileScanAs = UIs.textFieldsUI('Provide the following information about the tile scan that was analyzed',
                              tileScanQs,['']*len(tileScanQs))

########################################################################
########## IDENTIFY THE RESEARCHERS WHO ANALYZED THESE FIELDS ##########
########################################################################

# Identify all sub-directories containing the cell labelings performed
# by the various researchers
RALabelDirs = ImageFiles.findSubDirs(cellLabelDir)

# One of these sub-directories might be for someone who re-labeled field
# the other researchers already labeled. Ignore this directory.
RALabelDirs = [RALabelDir for RALabelDir in RALabelDirs if 'Relabeled-By-' not in RALabelDir]

# For each directory, identify the initials of the researcher who worked
# on the fields of view
RAInitials = [re.match('Researcher-(.+)',RALabelDir).group(1) for RALabelDir in RALabelDirs]

########################################################################
############### IDENTIFY THE SIZE OF THESE FIELDS OF VIEW ##############
########################################################################

# The name of the directory above the folder specified by the user of
# this plugin at the beginning will contain information about the size
# of the field of view. Get the name of this folder.
fieldSizeDir = os.path.basename(os.path.dirname(cellLabelDir))

# Use this directory name to get the intended size of the field of view.
regex = re.compile('(?P<Size>(?:\d|\.)+)[a-zA-z]+Fields_(?P<Overlap>(?:\d|\.)+)(?P<Units>[a-zA-z]+)Overlap')
matches = regex.match(str(fieldSizeDir)).groupdict()
fieldOverlap = float(matches['Overlap'])
fieldOverlapUnits = matches['Units'] + 's'
fieldSize = float(matches['Size'])

########################################################################
################ IDENTIFY THE PHYSICAL LOCATION OF THESE ###############
################## FIELDS OF VIEW ON THE SOURCE IMAGE ##################
########################################################################

# There will be a csv file storing the physical coordinates of each fiel
# of view under the appropriate field of view folder. Get the path to
# this file.
coordCsvPath = ImageFiles.findImgsInDir(os.path.join(cellLabelDir,'..','..',
                                                     '..','FieldsOfView',
                                                     fieldSizeDir),
                                        '.csv','.*FieldLocations_.*')

# Read these field of view coordinates into a python dictionary
fovCoordsDict = DataFiles.csv2dict(coordCsvPath)

# Store a list of all the column names in the field of view coordinate
# csv file
fovCoordCsvCols = fovCoordsDict.keys()

# Identify the column name for the x/y coordinate and area of the field
# of view
xCoordCol = [col for col in fovCoordCsvCols if 'X_Coordinate_In_' in col][0]
fovCoordCsvCols.remove(xCoordCol)
yCoordCol = [col for col in fovCoordCsvCols if 'Y_Coordinate_In_' in col][0]
fovCoordCsvCols.remove(yCoordCol)
areaCoordCol = [col for col in fovCoordCsvCols if 'Area_In_' in col][0]
del fovCoordCsvCols

# Store a list of the column names for the field of view coordinates
fovCoordCols = [xCoordCol, yCoordCol]

########################################################################
######### COMBINE ALL MEASUREMENTS OBTAINED BY ALL RESEARCHERS #########
########################################################################

# Initialize a python dictionary that will merge all of the data stored
# in our field of view quantification csv files. Initialize a column in
# this dictionary storing the researcher who labeled the field of view.
mergedFieldQuantDict = {'Rater': []}

# Initialize a python dictionary that will merge all of the data stored
# in our cell quantification csv files. Initialize a column in
# this dictionary storing the researcher who labeled the cell.
mergedCellQuantDict = {'Rater': []}

# Loop across all researchers who analyzed the fields of view
for r in range(len(RALabelDirs)):

    # Identify all csv files containing the cell density and composition
    # measurements for each field of view
    fieldQuantCsvs = ImageFiles.findImgsInDir(os.path.join(cellLabelDir,
                                                           RALabelDirs[r],
                                                           'Quantifications_By_Field'),
                                              '.csv','Field-Quantifications_Field-.*')

    # Loop across all field of view quantification csv files
    for fieldQuantCsv in fieldQuantCsvs:

        # Read the csv file into a python dictionary
        quants4FieldDict = DataFiles.csv2dict(fieldQuantCsv)

        # Store the current field of view number
        iFov = int(quants4FieldDict['Field_of_View_Number'][0])

        # Loop across the keys for the field of view location and area
        for key in fovCoordCols + [areaCoordCol]:

            # Store the field of view location and area in the
            # dictionary
            quants4FieldDict[key] = [fovCoordsDict[key][iFov-1]]

        # Add the data from this field of view to our merged dictionary
        mergedFieldQuantDict = DataFiles.mergeDataDicts([mergedFieldQuantDict,
                                                         quants4FieldDict])

    # When we merge our dictionaries, the list stored under the 'Rater'
    # key will be populated with NaNs since 'Rater' isn't a key in
    # quants4FieldDict. Identify the index of these nans ...
    iNan = next((i for i,
                 v in enumerate(mergedFieldQuantDict['Rater']) if v != v),
                -1)
    # ... and then fill in these nans with the appropriate rater initials
    mergedFieldQuantDict['Rater'][iNan:] = [RAInitials[r]]*(len(mergedFieldQuantDict['Rater']) - iNan)

    # Identify all csv files containing information about all cells in
    # each field of view
    cellQuantCsvs = ImageFiles.findImgsInDir(os.path.join(cellLabelDir,
                                                          RALabelDirs[r],
                                                          'Quantifications_By_Cell'),
                                             '.csv','Cell-Quantifications_Field-.*')

    # Loop across all cell quantification csv files
    for cellQuantCsv in cellQuantCsvs:

        # Read the csv file into a python dictionary
        cellsInFieldDict = DataFiles.csv2dict(cellQuantCsv)

        # Get the field of view the cells are contained in
        iFov = ImageFiles.getFieldNumber(cellQuantCsv)

        # Loop across the data columns storing the coordinates of our
        # ROIs
        for key in fovCoordCols:

            # Store the physical coordinates of the field of view on the
            # source image
            fovCoords = float(str(fovCoordsDict[key][iFov-1]))

            # All of the physical coordinates saved in the csv
            # containing information about the cells in the field of
            # view are relative to an origin at the center of the field.
            # Transform these physical coordinates into the space of our
            # source image.
            cellsInFieldDict[key] = list(map(lambda coord : float(str(coord)) + fovCoords,
                                             cellsInFieldDict[key]))

        # Compute the number of cells that were in this field of view
        nCellsInFoV = len(cellsInFieldDict[key])

        # Add a column for this python data dictionary storing the field
        # of view these cells belong to
        cellsInFieldDict['Field_of_View_Number'] = [iFov]*nCellsInFoV

        # Add the cellular data from this field of view to our merged
        # dictionary
        mergedCellQuantDict = DataFiles.mergeDataDicts([mergedCellQuantDict,
                                                        cellsInFieldDict])

    # When we merge our dictionaries, the list stored under the 'Rater'
    # key will be populated with NaNs since 'Rater' isn't a key in
    # cellsInFieldDict. Identify the index of these nans ...
    iNan = next((i for i,
                 v in enumerate(mergedCellQuantDict['Rater']) if v != v),
                -1)
    # ... and then fill in these nans with the appropriate rater initials
    mergedCellQuantDict['Rater'][iNan:] = [RAInitials[r]]*(len(mergedCellQuantDict['Rater']) - iNan)

# Compute the total number of elements in each python dictionary
totNFoVs = DataFiles.getNElementsInDict(mergedFieldQuantDict)
totNCells = DataFiles.getNElementsInDict(mergedCellQuantDict)

# Loop across all pieces of information we want to add to these data
# files so we can know about the source image
for t in range(len(tileScanQs)):

    # Add this information to each of our python dictionaries
    mergedFieldQuantDict[tileScanQs[t]] = [tileScanAs[t]]*totNFoVs
    mergedCellQuantDict[tileScanQs[t]] = [tileScanAs[t]]*totNCells

# Add the amount of overlap the full field of view displayed to the RAs
# extends into neighboring fields
mergedFieldQuantDict['Field_Overlap_in_{}'.format(fieldOverlapUnits)] = [fieldOverlap]*totNFoVs

# Identify the name of our source image using the last csv file path we
# opened. We will use this later when saving our data files.
sourceImgName = re.match('^.*Cell-Quantifications_Field-\d+_(.+$)',
                         cellQuantCsv).group(1)

########################################################################
### IDENTIFY THE SIZE AND ROTATION OF THE FIELDS OF VIEW WE ANALYZED ###
########################################################################

# Get a list of the nuclear segmentations generated by the last RA we
# looped across above
nucSegFiles = ImageFiles.findImgsInDir(os.path.join(cellLabelDir,
                                                    RALabelDirs[r],
                                                    '*_Segmentations'),
                                       None,'.+-Segmentation_Field-.+')

# Open up the first nuclear segmentation file we found
nucSeg = ImagePlus(nucSegFiles[0])
del nucSegFiles

# Store the calibration of our fields of view
imgCal = nucSeg.getCalibration()

# Store the center of the image in pixels
fovCenter = (float(nucSeg.getWidth())/2.0,float(nucSeg.getHeight())/2.0)

# Store one half of the true field of view size in pixels
fieldSize = imgCal.getRawX(fieldSize)
halfFieldSize = fieldSize / 2.0

# Locate the text file storing how much our fields of view were rotated
rotFilePath = ImageFiles.findImgsInDir(os.path.join(cellLabelDir,'..','..',
                                                '..'),'.txt',
                                   'RotationInDegrees_.*')

# Open the text file
with open(rotFilePath,'r+') as rotFile:

    # Read the angle saved in the text file. The rotation needs to be
    # transformed to make sure it's divisible by 90 and the sign needs
    # to be flipped
    rotation = float(rotFile.read()) % -90

########################################################################
################ COMBINE ALL LABELED CELLS AND ANALYZED ################
#################### FIELDS INTO COMPOSITE ROI SETS ####################
########################################################################

# Identify all roi sets containing labeled cells
cellROIFiles = ImageFiles.findImgsInDir(os.path.join(cellLabelDir,
                                                     'Researcher-*',
                                                     'Cell_Labeling_By_Field'),
                                        None,'Cell_Labeling_Field-.+')

# Initialize a list of all cell labelings across the source image
allCellLabels = []

# Initialize a list of all fields of view on the source image that were
# analyzed
analyzedFovROIs = []

# Store a list of the field of view x coordinates, this will be used
# later to sort the above list of analyzed field of view ROIs
analyzedFovXCoords = []

# Loop across all ROI sets
for cellROIFile in cellROIFiles:

    # Open the ROI set
    cellROISet = ROITools.openROIFile(cellROIFile)

    # Check to make sure that this ROI set is a list and not a single
    # ROI
    if not isinstance(cellROISet,list):
        cellROISet = [cellROISet]

    # Identify the field of view number associated with this ROI set
    iFov = ImageFiles.getFieldNumber(cellROIFile)

    # Get the x and y coordinates of this field of view in physical
    # units and convert them into pixel units
    xFov = imgCal.getRawX(float(fovCoordsDict[xCoordCol][iFov-1]))
    yFov = imgCal.getRawY(float(fovCoordsDict[yCoordCol][iFov-1]))

    # Subtract the center of our field of view to compute our desired x
    # and y displacement for each ROI.
    dx = xFov - fovCenter[0]
    dy = yFov - fovCenter[1]

    # Move each ROI from the field space to the source image space
    [roi.setLocation(roi.getXBase() + dx, roi.getYBase() + dy) for roi in cellROISet]

    # Add these transformed cell labels to our composite data set
    allCellLabels.extend(cellROISet)

    # Create an ROI of the same size of our field of view centered at
    # our field of view
    basefovROI = Roi(xFov - halfFieldSize, yFov - halfFieldSize,
                     fieldSize,fieldSize)

    # Rotate this ROI appropriately
    fovROI = roirotator.rotate(basefovROI,rotation,xFov,yFov)

    # Rename this ROI based on what field of view number it belongs to
    fovROI.setName('Field-{}'.format(iFov))

    # Make these ROIs with white boundaries
    fovROI.setStrokeColor(Color.white)

    # Add this ROI to our composite list
    analyzedFovROIs.append(fovROI)

    # Add the x coordinate of the field of view to our list
    analyzedFovXCoords.append(xFov)

# Get a list of all fields of view numbers that did not contain any
# cells
noCellFovs = [int(mergedFieldQuantDict['Field_of_View_Number'][i]) for i in range(len(mergedFieldQuantDict['Total_N_Cells'])) if int(mergedFieldQuantDict['Total_N_Cells'][i]) < 1]

# Generate field of view ROIs for these fields that did not contain any
# cells
for iFov in noCellFovs:

    # Get the x and y coordinates of this field of view in physical
    # units and convert them into pixel units
    xFov = imgCal.getRawX(float(fovCoordsDict[xCoordCol][iFov-1]))
    yFov = imgCal.getRawY(float(fovCoordsDict[yCoordCol][iFov-1]))

    # Create an ROI of the same size of our field of view centered at
    # our field of view
    basefovROI = Roi(xFov - halfFieldSize, yFov - halfFieldSize,
                     fieldSize,fieldSize)

    # Rotate this ROI appropriately
    fovROI = roirotator.rotate(basefovROI,rotation,xFov,yFov)

    # Rename this ROI based on what field of view number it belongs to
    fovROI.setName('Field-{}'.format(iFov))

    # Make these ROIs with white boundaries
    fovROI.setStrokeColor(Color.white)

    # Add this ROI to our composite list
    analyzedFovROIs.append(fovROI)

    # Add the x coordinate of the field of view to our list
    analyzedFovXCoords.append(xFov)

########################################################################
######## ORDER OUR ROI AND DATA SETS BY INCREASING X COORDINATE ########
########################################################################

# Get a list of all the x coordinates of all cells in our ROI set
allCellXCoords = [roi.getXBase() for roi in allCellLabels]

# Sort our list of all cell labels based on the x coordinate of these
# ROIs
sortedCellLabels = [cell for _,cell in sorted(izip(allCellXCoords,allCellLabels))]

# Repeat the above for our list of ROIs marking fields of view that were
# analyzed
sortedFovROIs = [fov for _,fov in sorted(izip(analyzedFovXCoords,analyzedFovROIs))]

# Save this final list of ROIs marking the fields of view that were
# analyzed from the source image
ROITools.saveROIs(sortedFovROIs,
                  os.path.join(cellLabelDir,'Analyzed_{}_{}.zip'.format(fieldSizeDir,
                                                                        os.path.splitext(sourceImgName)[0])))

########################################################################
################### COLOR NUCLEI BY LABELED CELL TYPE ##################
########################################################################

# Get a list of all the unique cell types in our data set
cellTypes = sorted(list(set(mergedCellQuantDict['Cell_Type'])))

# Store a list of all colors available
colors = ['lightGray','cyan','magenta','yellow','green','blue','red','black',
          'darkGray','gray','orange','pink','white']

# Ask the user to specify how they would like to color these ROIs by
# cell type
cellTypeColors = UIs.textFieldsUI('Specify the color you would like to use for the ROIs of each cell type',
                              cellTypes,colors[:len(cellTypes)])

# Loop across all individual cells
for roi in sortedCellLabels:

    # Identify how we want to color this ROI
    roiSolidColor = getattr(Color,cellTypeColors[cellTypes.index(roi.getName())])

    # Make a more transparent version of this color
    roiColor = Color(roiSolidColor.getRed(),roiSolidColor.getGreen(),
                     roiSolidColor.getBlue(),200)

    # Set the color of our ROI
    roi.setStrokeColor(roiColor)
    roi.setFillColor(roiColor)

# Save our final set of cell ROIs
ROITools.saveROIs(sortedCellLabels,
                  os.path.join(cellLabelDir,
                               'Cell-Labeling_{}.zip'.format(os.path.splitext(sourceImgName)[0])))

# Save the composite csv files under our input directory
DataFiles.dict2csv(mergedFieldQuantDict,
                   os.path.join(cellLabelDir,
                                'Field-Quantifications_{}'.format(sourceImgName)))
DataFiles.dict2csv(mergedCellQuantDict,
                   os.path.join(cellLabelDir,
                                'Cell-Quantifications_{}'.format(sourceImgName)))
