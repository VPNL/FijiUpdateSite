#@ File(label='Where are your original semi-automated cell labels for this field of view size located?',style='directory') input_dir
#@ Float(label='What percent of these original cell labels would you like to re-label?',style='slider',value=10,min=0,max=100) percent2relabel
#@ String(label='What are the initials of the researcher who will be re-labeling these fields?',value='AAR') relabeler

'''
Randomly Select Fields To Relabel



AR April 2022
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import java file object so we can ask the user for the directory with
# the original cell labelings
from java.io import File

# Convert the directory with the original cell labelings from a java
# File to a string
inputDir = input_dir.getAbsolutePath()

# Convert the percent of all files to relabel into a proportion
frac2relabel = percent2relabel / 100.0

# Import our image files module so we can locate files and folders and
# make soft links
from ImageTools import ImageFiles

# Import os so we can work with file paths
import os

# Import random so we can randomly choose with fields to re-label
import random

# Import ceil so we can round up
from math import ceil

# Import regular expressions so we can search strings for expressions
import re

# Import copyfile from shutil so we can copy files
from shutil import copyfile

########################################################################
######## FIND ALL FIELDS OF VIEW THAT WERE ORIGINALLY SEGMENTED ########
########################################################################

# Identify all sub-directories of the input folder. These sub-
# directories will contain all of the original labelings made by each RA
origRALabelDirs = ImageFiles.findSubDirs(inputDir)

# Make sure that origRALabelDirs is a list. It will be a single string
# if there was only one RA 
if not isinstance(origRALabelDirs,list):
	origRALabelDirs = [origRALabelDirs]

# Look inside the first RA folder and get all of it's sub-directories
origSubDirs = ImageFiles.findSubDirs(os.path.join(inputDir,origRALabelDirs[0]))

# Some of these sub-directories will have the unlabeled fields that were
# randomly assigned to this first RA. Identify all of these unlabeled
# field directories
unlabeledFieldDirs = [origSubDir for origSubDir in origSubDirs if '_Unlabeled_Fields' in origSubDir]
del origSubDirs, origSubDir

########################################################################
##### RANDOMLY SELECT A SUBSET OF THESE FIELDS OF VIEW TO RE-LABEL #####
########################################################################

# Start a list of lists that will store all of the unlabeled fields that
# we want to re-label. The first list will have the same length as the
# number of unlabeled field directories. The sub-lists will have a
# length equivalent to the number of fields we are re-labeling
unlabeledFiles4Relabel = [[] for i in range(len(unlabeledFieldDirs))]

# Loop across all researchers who performed the original labelings
for origRADir in origRALabelDirs:

    # Get all of the unlabeled field file names within the first
    # unlabeled field directory
    filesAssigned2RA = ImageFiles.findImgsInDir(os.path.join(inputDir,origRADir,unlabeledFieldDirs[0]))

    # Get a list of all of the field numbers assigned to this RA
    fieldsAssigned2RA = [ImageFiles.getFieldNumber(fileAssigned) for fileAssigned in filesAssigned2RA]

    # Randomly re-order this list of field numbers associated with this
    # RA
    random.shuffle(fieldsAssigned2RA)

    # Select our desired sub-set of of fields of view
    fields2Relabel = fieldsAssigned2RA[:int(ceil(frac2relabel * len(fieldsAssigned2RA)))]

    # Write out a regular expression search phrase that can be used to
    # located files associated with these field of view numbers
    searchPhrase = '.*Field-((' + ')|('.join(map(str,fields2Relabel)) + '))_.*'

    # Loop across all unlabeled field directories
    for iDir in range(len(unlabeledFieldDirs)):

        # Add all of the appropriate images we would like to relabel to
        # our list
        unlabeledFiles4Relabel[iDir] += ImageFiles.findImgsInDir(os.path.join(inputDir,
                                                                              origRADir,
                                                                              unlabeledFieldDirs[iDir]),
                                                                 None,
                                                                 searchPhrase)

########################################################################
############# ASSIGN THESE FIELDS OF VIEW IN A RANDOM ORDER ############
########################################################################

# Create new folders where the fields that need to be relabeled will
# reside
ImageFiles.makedir(os.path.join(inputDir,'Relabeled-By-{}'.format(relabeler)))
[ImageFiles.makedir(os.path.join(inputDir,'Relabeled-By-{}'.format(relabeler),unlabeledFieldDir)) for unlabeledFieldDir in unlabeledFieldDirs]

# Generate a list of all field of view indicies in
# unlabeledFiles4Relabel
iFovs = range(len(unlabeledFiles4Relabel[0]))

# Randomly shuffle the order of these indicies
random.shuffle(iFovs)

# Start a counter that will indicate the order that the fields of view
# should be re-labeled
i = 1

# Loop across all fields of view that we want to re-label
for iFov in iFovs:

    # Loop across all unlabeled field directories
    for iDir in range(len(unlabeledFieldDirs)):

        # Identify the name of the field of view file we are linking,
        # independent of any leading numbers used to indicate the order
        # the original labeler was to process the images
        fovFName = re.findall('.*\d+(Field-.*)',unlabeledFiles4Relabel[iDir][iFov])[0]

        # Create a soft link from the originally labeled file to this
        # new space where the RA will re-label
        ImageFiles.makeSoftLink(unlabeledFiles4Relabel[iDir][iFov],
                                os.path.join(inputDir,
                                             'Relabeled-By-{}'.format(relabeler),
                                             unlabeledFieldDirs[iDir],
                                             str(i) + fovFName))

    # Increase our counter
    i += 1

# Identify the location of our true field of view boundary ROI so we can
# copy it over to our relabeling folder
fovBoundaryPath = ImageFiles.findImgsInDir(os.path.join(inputDir,
                                                        origRALabelDirs[0]),
                                           '.roi','FieldBoundary')

# Store just the name of this field of view boundary roi file
_,fovBoundaryFName = os.path.split(fovBoundaryPath)

# Copy the true field of view boundary ROI to our new relabeling folder
copyfile(fovBoundaryPath,
         os.path.join(inputDir,'Relabeled-By-{}'.format(relabeler),
         fovBoundaryFName))
