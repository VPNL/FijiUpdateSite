#@ File(label='Where are all of the cell labelings your researchers have completed?',style='directory') dataDir

'''
Compile CSVs

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
regex = re.compile('.*Fields_(?P<Overlap>(?:\d|\.)+)(?P<Units>[a-zA-z]+)Overlap')
matches = regex.match(str(fieldSizeDir)).groupdict()
fieldOverlap = int(matches['Overlap'])
fieldOverlapUnits = matches['Units'] + 's'

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

# Identify the name of our source image using the last csv file path we
# opened
sourceImgName = re.match('^.*Cell-Quantifications_Field-\d+_(.+$)',
                         cellQuantCsv).group(1)

# Save the composite csv files under our input directory
DataFiles.dict2csv(mergedFieldQuantDict,
                   os.path.join(cellLabelDir,
                                'Field-Quantifications_{}'.format(sourceImgName)))
DataFiles.dict2csv(mergedCellQuantDict,
                   os.path.join(cellLabelDir,
                                'Cell-Quantifications_{}'.format(sourceImgName)))
