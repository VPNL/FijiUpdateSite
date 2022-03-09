#@ File(label='Where are your SemiautoCellLabels located?',style='directory') input_dir
#@ String(label='What is the name of the marker you want to analyze at different field of view sizes?',value='NeuN') markerOfInterest

'''
Test Smaller Fields

AR Mar 2022

TODO: export all measurements at each field of view size so we can make
      box plots
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so we can ask the user to specify the folder
# containing the semi auto cell labels
from java.io import File

# Convert input_dir from a java.io.File object to a string
dataDir = input_dir.getAbsolutePath()

# Import our ImageFiles module from ImageTools so we can search for
# files of interest
from ImageTools import ImageFiles

# Import os so we can join path elements
import os

# Import ROI tools so we can read ROI files
import ROITools

# Import ImagePlus object so we can open image
from ij import ImagePlus

# Open a dummy ImagePlus object so that after this command it will
# properly open image files
ImagePlus()

# Import our user interfaces
import UIs

# Import ImageJ's ROIEnlarger package
from ij.plugin import RoiEnlarger
roienlarger = RoiEnlarger()

# Import out statistics library so we can compute the coefficient of
# error
import Stats

# Import data files so we can write csv files
import DataFiles

########################################################################
#################### IDENTIFY SIZE OF FIELDS TO TEST ###################
########################################################################

# All of the semi auto cell labels should be distributed between various
# research assistants, each assigned a sub directory under
# SemiautoCellLabels. Identify these sub directories.
RADirs = [RADir for RADir in ImageFiles.findSubDirs(dataDir) if 'Researcher-' in RADir]

# Store the full file path to the first RA directory
frstRAPath = os.path.join(dataDir,RADirs[0])

# Search the first RA directory for the true field of view boundary ROI
fovROIFile = ImageFiles.findImgsInDir(frstRAPath,'roi','FieldBoundary')

# Open the field of view ROI
fovROI = ROITools.openROIFile(fovROIFile)
del fovROIFile

# Get the length of a side of this rotated field of view ROI
fovPxlSize = fovROI.getLength() / 4.0

# Search the first RA directory for a segmentation sub-directory
nucSegDir = [subDir for subDir in ImageFiles.findSubDirs(frstRAPath) if '_Segmentations' in subDir]
nucSegDir = nucSegDir[0]

# Get a list of all of the nuclear segmentations in this directory
nucSegs = ImageFiles.findImgsInDir(os.path.join(frstRAPath,nucSegDir),
                                   None,'-Segmentation_Field-')
del frstRAPath, nucSegDir

# Check to make sure nucSegs is a list and not just a character array
if not isinstance(nucSegs,list):
    nucSegs = [nucSegs]

# Open the first nuclear segmentation as an example to get the physical
# units of the field of view ROI
nucSeg = ImagePlus(nucSegs[0])
del nucSegs

# Get the calibration of this image so we can identify the size of our
# field of view
imgCal = nucSeg.getCalibration()
nucSeg.close()
del nucSeg

# Get the length units used in this image
lengthUnits = imgCal.getUnits()

# Get the size of the field of view in physical units
fovPhysicalSize = imgCal.getX(fovPxlSize)

# Ask the user to specify the size of the smallest field of view as well
# as the increment you want in between fields of view to test
[smallestFieldPhysical,fieldIncrementPhysical] = UIs.textFieldsUI('Specify what field of view sizes you would like to test',
                                                                  ['Smallest Field of View Size to Test in {}'.format(lengthUnits),
                                                                   'Difference in Size of Fields to Test in {}'.format(lengthUnits)],
                                                                  ['10','5'])

# Convert the incremental change in field of view size from physical
# units to pixels
fieldIncrementPxl = imgCal.getRawX(float(fieldIncrementPhysical))

# Convert the smallest field size from a string to a float
smallestFieldPhysical = float(smallestFieldPhysical)

########################################################################
################## TEST DIFFERENT FIELD OF VIEW SIZES ##################
########################################################################

# Start a dictionary that will store our data
dataDict = {'Field_of_View_Width_in_{}'.format(lengthUnits): [],
            'Total_N_Cells_Per_{}_Squared'.format(lengthUnits): [],
            'N_{}_Per_{}_Squared'.format(markerOfInterest,lengthUnits): [],
            'Total_N_Cells': [],
            'N_{}'.format(markerOfInterest): [],
            'Field_of_View_Number': []}

# Loop across all RAs that worked on fields of view
for subDir in RADirs:

    # Get the full path to the RA directory
    RADir = os.path.join(dataDir,subDir)

    # All fields of view will have a .zip or .roi file with all of the
    # nuclear ROIs within the field of view
    fovNucSegsPaths = ImageFiles.findImgsInDir(os.path.join(RADir,'Cell_Labeling_By_Field'),
                                               None,
                                               'Cell_Labeling_Field')

    # Check to make sure there's at least one file containing nuclear
    # labels
    if len(fovNucSegsPaths) > 0:

        # Make sure that there is more than one path listed
        if not isinstance(fovNucSegsPaths,list):

            fovNucSegsPaths = [fovNucSegsPaths]

        # Loop across all sets of nuclear segmentations
        for fovNucSegsPath in fovNucSegsPaths:

            # Get the field of view number for this segmentation
            fovNum = ImageFiles.getFieldNumber(fovNucSegsPath)

            # Get all of the labeled nuclei ROIs for this field of view
            fovLabeledNucs = ROITools.openROIFile(fovNucSegsPath)

            # Make a copy of the original field of view boundary ROI
            fovROI_cp = fovROI.clone()

            # Store the length of a side of the field of view in
            # physical units
            fovSidePhysicalLength = imgCal.getX(fovROI_cp.getLength() / 4.0)

            # Loop across all field of view sizes that we want to test
            while fovSidePhysicalLength > smallestFieldPhysical:

                # Store the length of the side of the field of view
                dataDict['Field_of_View_Width_in_{}'.format(lengthUnits)].append(fovSidePhysicalLength)

                # Store the field of view number in our data set
                dataDict['Field_of_View_Number'].append(fovNum)

                # Compute the area of the field of view
                fovArea = fovSidePhysicalLength ** 2

                # Identify which nuclear ROIs are contained within the
                # field of view of this size
                nucsInSmallFov = ROITools.ROIsInArea(fovLabeledNucs,fovROI_cp)

                # Get the total number of nuclei in the field of view
                totNNucs = float(len(nucsInSmallFov))

                # Store the total number of nuclei in this field of view
                dataDict['Total_N_Cells'].append(totNNucs)

                # Store the density of all cells in this field of view
                dataDict['Total_N_Cells_Per_{}_Squared'.format(lengthUnits)].append(totNNucs / fovArea)

                # Check to see if there is at least one cell in the
                # field of view
                if totNNucs > 0:

                    # Count the number of nuclei with the marker we're
                    # interested in getting the CE for
                    nucsPositive4Marker = [nuc for nuc in nucsInSmallFov if markerOfInterest in nuc.getName()]

                    # Store the total number of nuclei expressing this
                    # marker
                    NNucsWithMarker = float(len(nucsPositive4Marker))
                    dataDict['N_{}'.format(markerOfInterest)].append(NNucsWithMarker)

                    # Store the density of this cell type in the field
                    # of view
                    dataDict['N_{}_Per_{}_Squared'.format(markerOfInterest,lengthUnits)].append(NNucsWithMarker / fovArea)

                else:

                    # Store the density and total number of this cell
                    # type in the field of view
                    dataDict['N_{}_Per_{}_Squared'.format(markerOfInterest,lengthUnits)].append(0.0)
                    dataDict['N_{}'.format(markerOfInterest)].append(0.0)

                # Shrink the field of view by our incremental factor
                fovROI_cp = roienlarger.enlarge(fovROI_cp,-float(fieldIncrementPxl)/ 2.0)

                # Store the length of a side of the new field of view in
                # physical units
                fovSidePhysicalLength = imgCal.getX(fovROI_cp.getLength() / 4.0)

# Save the results of this analysis to a csv file
DataFiles.dict2csv(dataDict,
                   os.path.join(dataDir,
                                'Analysis_of_{}_By_Field_Size.csv'.format(markerOfInterest)))
