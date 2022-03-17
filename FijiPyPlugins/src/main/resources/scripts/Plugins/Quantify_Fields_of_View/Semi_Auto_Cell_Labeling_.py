#@ File(label='Please select the folder containing the fields of view assigned to you.',style='directory') data_directory
#@ Short(label='Each field of view is assigned a number. Which field of view are you working on?', value=1) n_fov
#@ Float (label='Across how many z-levels would you like to quantify?', value=11) z_height

'''
Semi Auto Cell Labeling

This script can be used to semi automatically segment nuclei and label
them according to cell type (i.e., expression of markers imaged in
separate channels). The script is intended to be run after Randomly
Assign Fields. First, the user will be asked which marker (e.g., DAPI)
they want to have segmented (i.e., their nuclear marker). Then, the user
will be asked which marker they want to use to define their focus levels
across the z-stack. Next, the user will be asked to edit an
automatically produced segmentation of their nuclear stain. After
editing the segmentation, the user will be asked to check the cell type
labeling automatically predicted by this script based on the pixel
intensities of each stain. Finally, all results will be saved into
data files, along with the final segmentation and cell labelings.

INPUTS

    - data_directory (java.io.File): Randomly Assign Fields will create
                                     separate folders for all
                                     researchers currently analyzing a
                                     tile scan together. Here, specify
                                     the folder assigned to you (e.g.,
                                     Researcher-1) for the tile scan.

    - n_fov (int): Each field of view is ordered randomly and assigned a
                   number. Enter the field of view number here. If
                   you're just starting, enter '1' and then increase the
                   next time you run the script.

    - z_height (int): The z-height across which you want to quantify.
                      It's generally recommended to work across an
                      equivalent number of z-slices to get a total
                      z-height of 11 microns or so.

OUTPUTS

    The script will automatically produce 3 files within the same
    data_directory specified by the user. The first file is a
    segmentation of the nuclei in this field of view. The second is an
    ROI file containing all of the Fiji ROIs with appropriate cell
    labeling. The final is a csv file containing all of the
    quantifications performed semi-automatically by the script and the
    user.

AR Dec 2021
AR Feb 2022 Edited output to keep track of distance between cells and
            protein/transcript expression within each cell
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so we can ask the user to specify the folder
# containing the fields of view they would like to work on
from java.io import File

# Convert the data_directory java.io.File object to a string so that we
# know the path to the folder containing the fields the user wants to
# semi-manually label
dataDir = data_directory.getAbsolutePath()

del data_directory

# Import our libraries for working with image files as well as
# processing and displaying images
from ImageTools import ImageFiles, ImageProcessing, ImageDisplay

# Import regular expressions so we can parse strings for information
import re

# Import our UI library so we can ask the user to make choices
import UIs

# Import os so we can join path elements
import os

# Import ImagePlus so we can read image files and IJ so we can run
# macros commands
from ij import ImagePlus, IJ

# Open a dummy ImagePlus object so that after this command it will
# properly open image files
ImagePlus()

# Import ROITools so we can work with ROIs and ROI files
import ROITools

# Import datetime so we can keep track of how much time the user spends
# on manual edits and checks
from datetime import datetime

# Import WaitForUserDialog so we can give instructions to the user and
# wait for them to finish
from ij.gui import WaitForUserDialog

# Import the duplicator so we can copy images
from ij.plugin import Duplicator

# Initialize a duplicator object
duplicator = Duplicator()

# Import izip so we can iterate across multiple lists
from itertools import izip

# Import sequence matcher so that we can identify the longest common
# substring shared between two strings
from difflib import SequenceMatcher

# Import our statistics module so we can compute z-scores and the
# distance between cells
import Stats

# Import our data files module so we can write data files
import DataFiles

########################################################################
######### IDENTIFY THE MARKERS IMAGED IN THE DIFFERENT CHANNELS ########
########################################################################

# The marker names will be present in the subdirectories of our data
# directory. List out all subdirectories of our data directory
subDataDirs = ImageFiles.findSubDirs(dataDir)

# Define a regular expression to extract the marker name from the
# subdirectory
regex = re.compile('(?P<marker>.*)_Unlabeled_Fields')

# Loop across all sub directories and identify which contain the
# unlabeled fields of view
unlabeledFieldsDirs = [subDataDir for subDataDir in subDataDirs if '_Unlabeled_Fields' in subDataDir]
del subDataDirs, subDataDir

# Get the markers corresponding to each of these unlabeled fields of
# view directories
markers = [regex.match(unlabeledFieldsDir).groupdict()['marker'] for unlabeledFieldsDir in unlabeledFieldsDirs]
del unlabeledFieldsDirs, unlabeledFieldsDir, regex

# Ask the user which nuclear marker (e.g. DAPI) they would like to
# segment
marker2seg = UIs.whichChoiceUI('Specify the nuclear marker (e.g. DAPI) you would like to have segmented.',
                               'Marker: ',markers)

# Store a list of markers that will be labeled according to the nuclear
# marker segmentation, sort by alphabetical order
markers2label = sorted([marker for marker in markers if marker != marker2seg])
del markers, marker

# Ask the user which marker would they like to use to identify the
# center of the z-stack
marker2focus = UIs.whichChoiceUI('Which marker would you like to use to set the focus of your z-stack?',
                                 'Marker: ',markers2label)

########################################################################
######### COMPUTE THE Z-LEVELS ACROSS WHICH WE WANT TO QUANTIFY ########
########################################################################

# Store the file path to the image of the marker we want to use to
# define our focus planes
marker2focusPath = ImageFiles.findImgsInDir(os.path.join(dataDir,
                                                        '{}_Unlabeled_Fields'.format(marker2focus)),
                                            None,
                                            '{}{}Field-'.format(os.path.sep,
                                                                n_fov))
del marker2focus

# Read the image of the marker we want to focus on
marker2focusImp = ImagePlus(marker2focusPath)
del marker2focusPath

# Create a zStack object using this image so that we can see across what
# z-slices we want to quantify
marker2focusZStack = ImageProcessing.zStack(marker2focusImp)
marker2focusImp.close()
del marker2focusImp

# Identify the starting and ending z-levels to be included in our
# quantifications
zBounds4Quants = marker2focusZStack.setZLevels4Focus(z_height)
marker2focusZStack.orig_z_stack.close()
del marker2focusZStack, z_height

# Start a python dictionary that will store various aspects about this
# field of view we are quantifying. Add in the bottom and top z-slice
# used for quantification
fieldQuants = {'Bottom_Z_Slice_Quantified': [zBounds4Quants[0]]}
fieldQuants['Top_Z_Slice_Quantified'] = [zBounds4Quants[-1]]

########################################################################
####################### SEGMENT OUR NUCLEAR STAIN ######################
########################################################################

# Store the file path to the image of our nuclear marker
nucPath = ImageFiles.findImgsInDir(os.path.join(dataDir,
                                                '{}_Unlabeled_Fields'.format(marker2seg)),
                                   None,
                                   '{}{}Field-'.format(os.path.sep,
                                                       n_fov))

# Read the nuclear marker image
nucImp = ImagePlus(nucPath)
del nucPath

# Create a z-stack object for this nuclear stain
nucStack = ImageProcessing.zStack(nucImp)

# Perform a maximum intensity projection across the z-levels contained
# in zBounds4Quants
nucMaxProj = nucStack.maxProj(zBounds4Quants)

# Shorten the z-stack so that only the z-levels within zBounds4Quants
# is included
nucShortZStack = nucStack.cropZStack()
nucStack.orig_z_stack.close()
del nucStack

# Segment the nuclear maximum intensity projection
nucSeg = ImageProcessing.segmentImg(nucMaxProj)

# Overlay the segmentation on top of the maximum intensity projection
nucSegOverlay = ImageDisplay.overlayImages([nucMaxProj,nucSeg])
nucSeg.close()
del nucSeg

# Get a blurred image of the nuclear maximum intensity projection that
# might be useful for manual segmentation editing
nucBlur = ImageProcessing.smoothImg(nucMaxProj)

# Find the file containing our field boundary ROI
fieldBoundROIFile = ImageFiles.findImgsInDir(dataDir,'roi',
                                             'pxlFieldBoundary')

# Open the field boundary ROI file to get the ROI
fieldBoundROI = ROITools.openROIFile(fieldBoundROIFile)
del fieldBoundROIFile

# Load the ROI File to the ROI Manager
ROITools.addROIs2Manager(fieldBoundROI)

# Display the overlay between the nuclear segmentation and the max
# projection, the gaussian blurred maximum projection, and the shortened
# z-stack to the user
nucBlur.show()
nucShortZStack.show()
nucSegOverlay.show()

# Add the true field of view boundary ROI to all open images
nucBlur.setRoi(fieldBoundROI)
nucShortZStack.setRoi(fieldBoundROI)
nucSegOverlay.setRoi(fieldBoundROI)

# Make sure that the active channel of the segmentation overlay is the
# segmentation, rather than the maximum intensity projection
nucSegOverlay.setC(2)

# Open the channels tool for the user to check the segmentation against
# the original image
IJ.run("Channels Tool...")

# Get the current time so we can figure out how long it takes for the
# user to edit the nuclear segmentation
time_b4_seg = datetime.now()

# Instruct the user to manually edit the the automatically produced DAPI
# segmentation
WaitForUserDialog('Perform edits on the automatically-produced nuclei segmentation in magenta.\nUse the max projection in green and your z-stack image as references to\nguide your edits. You can also use the Gaussian Blurred image to label\ncurrently unlabeled nuclei using the wand tool.\n\nPress "OK" when done with your edits.').show()

# Get the time now that the manually edited segmentation is complete
time_after_seg = datetime.now()

# Compute the number of seconds that it took for the user to manually
# edit the segmentation
time2seg = (time_after_seg.getTime() - time_b4_seg.getTime()) / 1000.0
del time_after_seg, time_b4_seg

# Add the amount of time needed to correct the nuclear segmentation to
# our data dictionary
fieldQuants['Seconds_to_correct_{}_segmentation'.format(marker2seg)] = [time2seg]
del time2seg

# Close and hide the blurred image and shortened z-stack
nucBlur.close()
nucShortZStack.hide()
del nucBlur

# Clear any ROIs (for instance the field boundary ROI) from display on
# the overlay image and the short z stack
nucSegOverlay.deleteRoi()
nucShortZStack.deleteRoi()

# Grab the final nuclear segmentation from the overlay (the second
# channel in the overlay)
editedNucSeg = duplicator.run(nucSegOverlay,2,2)

# Close and delete the overlay image
nucSegOverlay.close()
del nucSegOverlay

# Convert the segmentation into a list of ROIs for each segmented
# nucleus
allNucROIs = ImageProcessing.segmentation2ROIs(editedNucSeg)

# Crop this list of ROIs so that they only contain those whose centers
# are contained within the true field boundary
nucROIs = ROITools.ROIsInArea(allNucROIs,fieldBoundROI)
del allNucROIs

# Store the total number of cell ROIs that need to be labeled by cell
# type
nCells2Lable = len(nucROIs)

# Invert all of the ROIs labeling the cell nuclei so that they label
# all pixels outside of the cell nuclei (aka, the background of the
# image)
notNucROI = ROITools.getBackgroundROI(nucROIs,fieldBoundROI,editedNucSeg)

# Compute the area of the field of view we quantified from
[field_area,field_length_units] = ROITools.getROIArea(fieldBoundROI,editedNucSeg)

########################################################################
####################### LABEL CELLS BY CELL TYPE #######################
########################################################################

# Store the path to each of the images of cells that need to be labeled
markers2LabelPaths = [ImageFiles.findImgsInDir(os.path.join(dataDir,
                                                            '{}_Unlabeled_Fields'.format(marker)),
                                               None,
                                               '{}{}Field-'.format(os.path.sep,
                                                                   n_fov)) for marker in markers2label]
del marker

# Read each of these images of the markers we want to label
markers2LabelImgs = [ImagePlus(path) for path in markers2LabelPaths]
del markers2LabelPaths, path

# Store a list of our predictions of the cell type for each nuclear ROI.
# Set default label to the same as our nuclear label.
predictedNucLabels = [marker2seg] * nCells2Lable

# Initialize a list that will store the cropped image stacks for all
# markers so that the z levels line up with what was used for the
# nuclear segmentation
markers2LabelShortStacks = []

# Initialize a list that will store all of the max projections of each
# non-nuclear channel
labelMaxProjs = []

# Loop across all markers that need to be labeled
for m in range(len(markers2label)):

    # Create a z-stack object for this marker to label's z-stack
    labelStack = ImageProcessing.zStack(markers2LabelImgs[m])

    # Create a maximum intensity projection for this label, using only
    # the z levels we're focusing on
    labelMaxProjs.append(labelStack.maxProj(zBounds4Quants))

    # Compute a t-statistic comparing the gray level inside each nuclear
    # ROI with the gray level outside all of the nuclear ROIs using the
    # image of this marker. This t-statistic can tell us whether the
    # average intensity of the label within each nucleus is relatively
    # high, suggesting that the label is expressed by this cell.
    tStatsByNuc = ROITools.grayLevelTTest(nucROIs,notNucROI,
                                          labelMaxProjs[-1])

    # Loop across all nuclei
    for nuc in range(nCells2Lable):

        # Check to see if the t statistic for this nuclei and label was
        # high. Since the degrees of freedom will be very high since
        # we're comparing two large populations of pixels, t approaches
        # z and a statistic of 3 corresponds with a p of about 0.0005
        if tStatsByNuc[nuc] > 3:

            # Add this marker to our predicted cell type
            predictedNucLabels[nuc] += '-' + markers2label[m]

    # Store the shortened image stack in our list of short image stacks
    markers2LabelShortStacks.append(labelStack.cropZStack())
[markers2LabelImgs[m].close() for m in range(len(markers2LabelImgs))]
labelStack.orig_z_stack.close()
del m, nuc, labelStack, tStatsByNuc, zBounds4Quants
del markers2LabelImgs, notNucROI

# Identify the number of this field of view
iFov = ImageFiles.getFieldNumber(nucShortZStack.getTitle())

# Add the field of view number to our data dictionary
fieldQuants['Field_of_View_Number'] = [iFov]

# Identify the longest string common between the file names for the
# nuclear short z stack and the first marker's short stack. This will
# serve as a template for our output file name.
sequence_matcher = SequenceMatcher(None,nucShortZStack.getTitle(),
                                   markers2LabelShortStacks[0].getTitle())
match = sequence_matcher.find_longest_match(0,
                                            len(nucShortZStack.getTitle()),
                                            0,
                                            len(markers2LabelShortStacks[0].getTitle()))
[outFileName,fileExt] = os.path.splitext('Field-{}'.format(iFov) + nucShortZStack.getTitle()[match.a:match.a + match.size])
del sequence_matcher, match

# If the outFileName ends with an underscore or a hyphen...
while outFileName.endswith(('_','-')):

    # Remove the last element of the file name
    outFileName = outFileName[:-1]

# Rename all of the nuclear ROIs to match their predicted cell type
[nucROIs[nuc].setName(predictedNucLabels[nuc]) for nuc in range(nCells2Lable)]
del predictedNucLabels, nuc

# Merge all of the shortened z-stacks for all markers in this image
mergedShortZStack = ImageDisplay.overlayImages(markers2LabelShortStacks + [nucShortZStack])
[markers2LabelShortStacks[m].close() for m in range(len(markers2LabelShortStacks))]
nucShortZStack.close()
del markers2LabelShortStacks, nucShortZStack

# Display the merged short stack
mergedShortZStack.show()

# Merge and display all of the max projections for all markers in this
# image
mergedMaxProj = ImageDisplay.overlayImages(labelMaxProjs)
mergedMaxProj.show()

# Display all of the ROIs labeled by cell type
ROITools.addROIs2Manager(nucROIs)
del nucROIs

# Store all of the color channels in the merged image in the order
# matching our list of markers to label
channelColors = ['Cyan', 'Magenta', 'Yellow', 'Gray', 'Green', 'Blue', 'Red']

# Open the channels tool so the user can turn channels on and off
IJ.run("Channels Tool...")

# Keep track of what time we start relabeling all of the cells
time_b4_labeling = datetime.now()

# Ask the user to check to make sure the cell labeling is correct
WaitForUserDialog('Check all ROIs in your ROI Manager to make sure they are appropriatly\nlabeled with the correct marker. Change the name of any ROI that is\nincorrectly labeled. Press OK when the labeles are correct.\n' + '\n'.join('%s: %s' % channel for channel in izip(channelColors[:len(markers2label)+1],markers2label+[marker2seg]))).show()

# Record the time now that the user has finished checking the cell
# labeling
time_after_labeling = datetime.now()

# Compute the number of seconds it took for the user to check the cell
# labeling
time2label = (time_after_labeling.getTime() - time_b4_labeling.getTime()) / 1000.0
del time_b4_labeling, time_after_labeling, channelColors

# Add the amount of time needed to correct the cell labels to our data
# dictionary
fieldQuants['Seconds_to_correct_cell_types'] = [time2label]
del time2label

# Close the overlay
mergedShortZStack.close()
del mergedShortZStack
mergedMaxProj.close()
del mergedMaxProj

# Get all of the ROIs in the ROI Manager
labeledNuclei = ROITools.getOpenROIs()

# Clear the ROI Manager
ROITools.clearROIs()

########################################################################
############## SAVE NUCLEAR SEGMENTATION AND LABELED ROIS ##############
########################################################################

# Check to make sure that all of these final ROIs are still contained
# within the true field of view boundary
labeledNuclei = ROITools.ROIsInArea(labeledNuclei,fieldBoundROI)

# Convert this list of labeled nuclei into a final segmentation mask
finalNucSeg = ImageProcessing.ROIs2Segmentation(labeledNuclei,
                                                editedNucSeg)

# Create a new data dictionary that will store the cell types of each
# segmented nucleus with their x and y coordinates in physical units
cellQuants = ROITools.getLabelsAndLocations(labeledNuclei,editedNucSeg)

# Make a directory where we will save this final nuclear segmentation
segDir = os.path.join(dataDir,'{}_Segmentations'.format(marker2seg))
ImageFiles.makedir(segDir)

# Save the final nuclear segmentation as a tif file
IJ.save(finalNucSeg,os.path.join(segDir,
                                 '{}-Segmentation_{}{}'.format(marker2seg,
                                                             outFileName,
                                                             fileExt)))
nucImp.close()
finalNucSeg.close()
del segDir,nucImp,finalNucSeg

# Make a directory where we will save these final nuclear ROIs labeled
# by cell type
roiDir = os.path.join(dataDir,'Cell_Labeling_By_Field')
ImageFiles.makedir(roiDir)

# Save all of the ROIs that were labeled by cell type
ROITools.saveROIs(labeledNuclei,os.path.join(roiDir,'Cell_Labeling_' + outFileName + '.zip'))
del roiDir

########################################################################
################ EXPORT FINAL MEASUREMENTS TO CSV FILES ################
########################################################################

# Store the number of nuclei labeled in our quantification dictionary
fieldQuants['Total_N_Cells'] = [len(labeledNuclei)]

# Add the nuclear density to our quantifications
fieldQuants['Total_N_Cells_Per_{}'.format(field_length_units)] = [fieldQuants['Total_N_Cells'][0] / field_area]

# Remake our notNucROI using only the ROIs that were labeled, in case
# any were deleted by the user
notNucROI = ROITools.getBackgroundROI(labeledNuclei,fieldBoundROI,editedNucSeg)
editedNucSeg.close()
del fieldBoundROI, editedNucSeg

# Store the SNR of the nuclear stain
fieldQuants['{}_SNR'.format(marker2seg)] = [ROITools.computeSNR(ROITools.combineROIs(labeledNuclei),
                                                                notNucROI,
                                                                nucMaxProj)]
nucMaxProj.close()
del nucMaxProj

# Loop across all markers to label
for m in range(len(markers2label)):

    # Get a list of all nuclear ROIs that were expressing this marker
    nucsExpressMrkr = [nucROI for nucROI in labeledNuclei if markers2label[m] in nucROI.getName()]

    # Check to see if there is at least one nuclear ROI that was found
    # to express this marker
    if len(nucsExpressMrkr) > 0:

        # Compute and store the approximate SNR of this stain
        fieldQuants['Approximate_{}_SNR'.format(markers2label[m])] = [ROITools.computeSNR(ROITools.combineROIs(nucsExpressMrkr),
                                                                        notNucROI,
                                                                        labelMaxProjs[m])]

    # Otherwise...
    else:

        # Store the approximate SNR of this stain as NaN
        fieldQuants['Approximate_{}_SNR'.format(markers2label[m])] = [float('nan')]

    # Get the average gray level inside each final ROI for this marker
    cellQuants['Mean_{}_Pixel_Intensity'.format(markers2label[m])] = [ROITools.getMeanGrayLevel(ROI,labelMaxProjs[m]) for ROI in labeledNuclei]
    labelMaxProjs[m].close()

    # Initialize a new list that will store the z-scored mean pixel
    # intensity for this channel
    cellQuants['{}_Z-Scored_Mean_Pixel_Intensity'.format(markers2label[m])] = []

del notNucROI, labelMaxProjs

# Loop across all nuclei that were labeled
for n in range(len(labeledNuclei)):

    # For this cell, get a list of all of the average pixel intensities
    # of each channel imaged
    avgPxlLevels = [cellQuants['Mean_{}_Pixel_Intensity'.format(m)][n] for m in markers2label]

    # Z-Score this list of average pixel intensities
    ZdPxlLevels = Stats.zScoreData(avgPxlLevels)

    # Add the z-scored average pixel intensity for this channel to our
    # dataset
    [cellQuants['{}_Z-Scored_Mean_Pixel_Intensity'.format(markers2label[m])].append(ZdPxlLevels[m]) for m in range(len(markers2label))]

# Store the plural version of the length units used in this image
plural_length_units = field_length_units[:field_length_units.index('_')] + 's'

# Compute the distace between all labeled nuclei
distBetweenNucs = Stats.distanceMatrix(cellQuants['X_Coordinate_In_{}'.format(plural_length_units)],
                                       cellQuants['Y_Coordinate_In_{}'.format(plural_length_units)])

# Get all of the labels that were assigned to each nuclei
labelsByNuclei = [labeledNucleus.getName() for labeledNucleus in labeledNuclei]
del labeledNuclei, labeledNucleus

# Get all of the unique cell type labels, making sure to include both
# all cell types in the field of view as well as all cell types we're
# expecting (i.e., cells expressing each marker)
cellTypes = list(set(labelsByNuclei + [marker2seg + '-' + marker2label for marker2label in markers2label] + [marker2seg]))
del marker2label, markers2label

# Loop across all cell types
for cellType in cellTypes:

    # Get the index of all nuclei that were labeled as this cell type
    nucsOfCellType = [int(n) for n in range(len(labelsByNuclei)) if labelsByNuclei[n] == cellType]

    # Count the number of cells of this cell type
    nCellType = len(nucsOfCellType)

    # Check to see if the cell type is just the name of the nuclear
    # marker
    if cellType == marker2seg:

        # Change the name of the cell type to other
        cellType = marker2seg + '-Only'

    # Initialize a list that will store the smallest distance between
    # each cell to this cell type
    cellQuants['Distance_to_next_nearest_{}_nucleus_in_{}'.format(cellType,plural_length_units)] = [float('nan')] * len(labelsByNuclei)

    # Check to see if at least one nucleus of this cell type is in this
    # field of view
    if nCellType > 0:

        # Loop across all nuclei that were labeled
        for n in range(len(labelsByNuclei)):

            # Get the distances from this nucleus all nuclei of this
            # cell type, excluding this nucleus
            distances2CellType = [distBetweenNucs[n][nucOfCellType] for nucOfCellType in nucsOfCellType if nucOfCellType != n]

            # Check to make sure there's at least one other nucleus of
            # this cell type
            if len(distances2CellType) > 0:

                # Store the smallest distance from this nucleus to the
                # next nearest nucleus of this cell type
                cellQuants['Distance_to_next_nearest_{}_nucleus_in_{}'.format(cellType,plural_length_units)][n] = min(distances2CellType)

    # Store the raw number of cells in this field of view
    fieldQuants['N_{}'.format(cellType)] = [nCellType]

    # Store the density of this cell type in the field of view
    fieldQuants['N_{}_Per_{}'.format(cellType,field_length_units)] = [nCellType / field_area]

    # Store the percent of all cells that are this cell type
    fieldQuants['Percent_of_cells_that_are_{}'.format(cellType)] = [(float(nCellType) / fieldQuants['Total_N_Cells'][0]) * 100.0]
del labelsByNuclei, cellTypes, cellType, nCellType, marker2seg
del field_area, field_length_units

# Make the directory where we want to store all of our cell
# quantifications
cellQuantsDir = os.path.join(dataDir,'Quantifications_By_Cell')
ImageFiles.makedir(cellQuantsDir)

# Save the field of view quantifications to a csv file
DataFiles.dict2csv(cellQuants,os.path.join(cellQuantsDir,
                                           'Cell-Quantifications_' + outFileName + '.csv'))
del cellQuantsDir, cellQuants

# Make the directory where we want to store all of our field
# quantifications
fieldQuantsDir = os.path.join(dataDir,'Quantifications_By_Field')
ImageFiles.makedir(fieldQuantsDir)

# Save the field of view quantifications to a csv file
DataFiles.dict2csv(fieldQuants,os.path.join(fieldQuantsDir,
                                            'Field-Quantifications_' + outFileName + '.csv'))
del fieldQuantsDir, dataDir, fieldQuants
