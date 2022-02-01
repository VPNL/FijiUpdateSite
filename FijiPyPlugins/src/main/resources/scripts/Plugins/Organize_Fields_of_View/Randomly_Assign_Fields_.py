#@ File(label='Where is your FieldsOfView folder located?',style='directory') fields_dir
#@ Short(label='How many researchers will quantify these fields of view?',value=2) NResearchers

'''
Randomly Assign Fields

This script can be used to randomly organize and assign fields of view
from various channels across a set number of researchers to perform
semi-automated cell labeling. This script is intended to be run after
Separate Image Into Fields.

INPUTS

    - fields_dir (java.io.File): FieldsOfView folder created from
                                 running Separate Image Into Fields.

    - NResearchers (int): The number of researchers amongst whom you
                          would like to distribute your fields of view

OUTPUTS

    The script will automatically randomize all fields of view created
    and sort them into separate folders organized by field of view size,
    markers imaged, and researchers working on these images.
    Specifically, soft links will be generated under a new folder called
    Quantifications under the main data directory that link back to the
    individual fields of view generated by Separate Image Into Fields.
    This way, we can conserve hard drive space.

AR Oct 2021
AR Jan 2022 Added UI so that the user can specify the initials of the
            RAs
'''

########################################################################
#################### IMPORT MODULES AND READ INPUT #####################
########################################################################

# Import Java File object so we can ask the user to specify the folder
# containing the images they would like to separate into unique fields
# of view
from java.io import File

# Convert the fields_dir java.io.File object to a string so we know the
# path to the folder containing the fields to be randomly assigned
fieldsDir = fields_dir.getAbsolutePath()

del fields_dir

# Import our UI module
import UI

# Import os so we can find subdirectories, make new directories and join
# path elements
import os

# Import tools that will allow us to work easily with files
from ImageTools import ImageFiles

# Import our user interface library
import UIs

# Import our ROI tools
import ROITools

# Import python's random package so we can randomly sort and assign
# fields of view
import random

# Import copyfile from shutil so we can copy files
from shutil import copyfile

########################################################################
############ ASK THE USER TO SPECIFY THE INITIALS OF ALL RAs ###########
########################################################################

# Store a list of strings that label each text field in the UI we will
# present to the user. Each string will take on the format 'Researcher
# X Initials' where X is replaced by the researcher number
initialsTextFieldLabels = ['Researcher {} Initials'.format(r) for r in range(NResearchers)]
del r

# The default initialis will just be the researcher number
defaultInitials = ['{}'.format(r) for r in range(NResearchers)]
del r

# Present the interface to the user so that we can get the initials of
# all the researchers
RAInitials = UIs.textFieldsUI('Specify the initials of all researchers who will quantify these fields of view.',
                          initialsTextFieldLabels,defaultInitials)
del initialsTextFieldLabels, defaultInitials

########################################################################
##################### IDENTIFY FIELD SIZE DESIRED ######################
########################################################################

# List all of the subdirectories of the field of view folder. These
# directory names will correspond with the different field sizes
# generated by running the Separate Image Into Fields script.
fieldSize = ImageFiles.findSubDirs(fieldsDir)

# Check to see if fields of multiple sizes have been generated
if isinstance(fieldSize,(tuple,list)):

    # If the user has made fields of view of more than one size, we'll
    # need to ask which field of view size they would like to use. Below
    # we make a UI to do this and get the chosen field size.
    fieldSize = UIs.whichChoiceUI('Which field of view size would you like to process?',
                                  'Field of view size:',fieldSize)

########################################################################
################# IDENTIFY DESIRED MARKERS TO QUANTIFY #################
########################################################################

# List all of the subdirectories of the field size subdirectory. These
# directory names will correspond with the different markers imaged in
# each channel.
markersImaged = ImageFiles.findSubDirs(os.path.join(fieldsDir,fieldSize))

# Ask the user which markers they would like to work on
markers2Assign = UIs.checkBoxUI('Which markers are you planning on analyzing?',
                                markersImaged)

del markersImaged

# Create a list of lists of all fields of view image files for each
# of the markers to assign to researchers
fieldsByMarker = [ImageFiles.findImgsInDir(os.path.join(fieldsDir,fieldSize,marker)) for marker in markers2Assign]

########################################################################
########### RANDOMIZE ALL ROWS AND COLUMNS OF FIELDS OF VIEW ###########
########################################################################

# After running the script Separate Image Into Fields, a zipped file
# containing all ROIs will be saved under the main data directory.
# Open this ROI file
fieldsROIs = ROITools.openROIFile(os.path.join(fieldsDir,'..','ROIs',fieldSize + '.zip'))

# Get all of the names of these ROIs. The list of these names will be
# equivalent to the list of all fields of view in the grid layed out
# previously in Separate Image Into Fields
fieldNames = [fieldROI.getName() for fieldROI in fieldsROIs]

del fieldsROIs

# Randomly shuffle this list of fields of view
random.shuffle(fieldNames)

########################################################################
############# DISTRIBUTE FIELDS OF VIEW AMONGST RESEARCHERS ############
########################################################################

# Divide up the fields of view so they are roughly equally distributed
# amongst the researchers
fieldsByResearcher = [fieldNames[i::NResearchers] for i in xrange(NResearchers)]

del fieldNames

# Loop across researchers that will be assigned fields of view
r = 0
for setOfFields in fieldsByResearcher:

    # Store the path to our new directory where this researcher's
    # assigned fields of view will be stored
    researcherOutDir = os.path.join(fieldsDir,'..','Quantifications',
                                    fieldSize,'-'.join(markers2Assign),
                                    'SemiautoCellLabels',
                                    'Researcher-' + RAInitials[r])

    # Make this folder if necessary
    ImageFiles.makedir(researcherOutDir)

    # Copy the true field of view boundary ROI to the folder where the
    # assigned fields will be organized for this researcher
    copyfile(os.path.join(fieldsDir,fieldSize,
                          fieldSize[:-1] + 'Boundary.roi'),
             os.path.join(researcherOutDir,
                          fieldSize[:-1] + 'Boundary.roi'))

    # Loop across markers imaged in various channels
    for imarker in range(len(markers2Assign)):

        # Create a directory for the assigned fields from this marker
        markerOutDir = os.path.join(researcherOutDir,
                                    markers2Assign[imarker] + '_Unlabeled_Fields')
        ImageFiles.makedir(markerOutDir)

        # Loop across all fields of view to assign to this researcher
        fieldNum = 1
        for fieldName in setOfFields:

            # Find the field where this marker is imaged that has the
            # correct field of view name
            iField2Assign = [iField for iField in range(len(fieldsByMarker[imarker])) if fieldName + '_' in fieldsByMarker[imarker][iField]][0]

            # Store the path to the field with the correct marker and
            # name, deleting it from our list
            field2Assign = fieldsByMarker[imarker].pop(iField2Assign)

            # Make a softlink for the field of view saved under
            # fieldPath under the researcher's directory for this marker
            # Store the field of view number in the soft link name
            ImageFiles.makeSoftLink(field2Assign,
                                    os.path.join(markerOutDir,str(fieldNum) + os.path.basename(field2Assign)))

            # Increase the field of view number
            fieldNum += 1

    # Increase the researcher number
    r += 1
