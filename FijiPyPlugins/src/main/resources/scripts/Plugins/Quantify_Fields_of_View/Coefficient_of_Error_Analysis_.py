#@ File(label='Where are your SemiautoCellLabels located?',style='directory') input_dir
#@ String(label='What is the name of the marker you want to calculate the CE for?',value='NeuN') marker4CE

'''
Coefficient of Error Analysis

AR Mar 2022
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

# Import java's summary statistics package so we can compute means and
# standard deviations to compute z-scores
from org.apache.commons.math3.stat.descriptive import DescriptiveStatistics as DSS

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

# Get the size of the field of view in physical units and round it
fovPhysicalSize = imgCal.getX(fovPxlSize)

# Ask the user to specify the size of the smallest field of view as well
# as the increment you want in between fields of view to test
[smallestFieldPhysical,fieldIncrementPhysical] = UIs.textFieldsUI('Specify what field of view sizes you would like to test',
                                                                  ['Smallest Field of View Size to Test in {}'.format(lengthUnits),
                                                                   'Difference in Size of Fields to Test in {}'.format(lengthUnits)],
                                                                  ['15','2.5'])

# Convert the incremental change in field of view size from physical
# units to pixels
fieldIncrementPxl = imgCal.getRawX(float(fieldIncrementPhysical))

# Convert the smallest field size from a string to a float
smallestFieldPhysical = float(smallestFieldPhysical)

########################################################################
################## TEST DIFFERENT FIELD OF VIEW SIZES ##################
########################################################################

# Start a dictionary that will store our data
dataDict = {'Field_of_View_Side_Length_in_{}'.format(lengthUnits): [],
            'Total_N_Cells_Per_{}_Squared'.format(lengthUnits): [],
            'N_{}_Per_{}_Squared'.format(marker4CE,lengthUnits): []}

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

            # Get all of the labeled nuclei ROIs for this field of view
            fovLabeledNucs = ROITools.openROIFile(fovNucSegsPath)

            # Make a copy of the original field of view boundary ROI
            fovROI_cp = fovROI.clone()

            # Store the length of a side of the field of view in physical
            # units
            fovSidePhysicalLength = imgCal.getX(fovROI_cp.getLength() / 4.0)

            # Loop across all field of view sizes that we want to test
            while fovSidePhysicalLength > smallestFieldPhysical:

                # Store the length of the side of the field of view
                dataDict['Field_of_View_Side_Length_in_{}'.format(lengthUnits)].append(round(fovSidePhysicalLength))

                # Compute the area of the field of view
                fovArea = fovSidePhysicalLength ** 2

                # Identify which nuclear ROIs are contained within the field
                # of view of this size
                nucsInSmallFov = ROITools.ROIsInArea(fovLabeledNucs,fovROI_cp)

                # Store the density of all cells in this field of view
                dataDict['Total_N_Cells_Per_{}_Squared'.format(lengthUnits)].append(float(len(nucsInSmallFov)) / fovArea)

                # Check to see if there is at least one cell in the field of view
                if len(nucsInSmallFov) > 0:

                    # Count the number of nuclei with the marker we're
                    # interested in getting the CE for
                    nucsPositive4Marker = [nuc for nuc in nucsInSmallFov if marker4CE in nuc.getName()]

                    # Store the density of this cell type in the field of view
                    dataDict['N_{}_Per_{}_Squared'.format(marker4CE,lengthUnits)].append(float(len(nucsPositive4Marker)) / fovArea)

                else:

                    # Store the density of this cell type in the field of view
                    dataDict['N_{}_Per_{}_Squared'.format(marker4CE,lengthUnits)].append(0.0)

                # Shrink the field of view by our incremental factor
                fovROI_cp = roienlarger.enlarge(fovROI_cp,-float(fieldIncrementPxl))

                # Store the length of a side of the new field of view in
                # physical units
                fovSidePhysicalLength = imgCal.getX(fovROI_cp.getLength() / 4.0)

# Get all unique field of view sizes
fovSizesTested = list(set(dataDict['Field_of_View_Side_Length_in_{}'.format(lengthUnits)]))

# Store the number of field of view sizes that were tested
nFovSizesTested = len(fovSizesTested)

# Create a dictionary to store just the coefficients of error at each
# field size
ceDict = {'Field_of_View_Side_Length_in_{}'.format(lengthUnits): [],
          'Coefficient_of_Error_Total_N_Cells_Per_{}_Squared'.format(lengthUnits): [],
          'Coefficient_of_Error_N_{}_Per_{}_Squared'.format(marker4CE,lengthUnits): []}

# Loop across each field size that was tested
for s in range(nFovSizesTested):

    # Store the size of the field of view
    ceDict['Field_of_View_Side_Length_in_{}'.format(lengthUnits)].append(dataDict['Field_of_View_Side_Length_in_{}'.format(lengthUnits)][s])

    # Compute and store the coefficient of error for the total cell
    # densities at this field of view size
    ceDict['Coefficient_of_Error_Total_N_Cells_Per_{}_Squared'.format(lengthUnits)].append(Stats.coefficientOfError(dataDict['Total_N_Cells_Per_{}_Squared'.format(lengthUnits)][s::nFovSizesTested]))

    # Compute and store the coefficient of error for the cell density
    # for the marker of interest
    ceDict['Coefficient_of_Error_N_{}_Per_{}_Squared'.format(marker4CE,lengthUnits)].append(Stats.coefficientOfError(dataDict['N_{}_Per_{}_Squared'.format(marker4CE,lengthUnits)][s::nFovSizesTested]))
