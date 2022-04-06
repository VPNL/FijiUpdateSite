#@ File(label='Where are all of your original and re-done cell labelings located?',style='directory') dataDir

'''
Quantify Reproducibility

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

# Import image files so we can search for files and directories
from ImageTools import ImageFiles

# Import os so we can work with paths
import os

# Import regular expressions so we can search strings for phrases
import re

# Import our ROI tools so we can open ROI files
import ROITools

# Import Image Plus so we can open up image files
from ij import ImagePlus
ImagePlus()

# Import our data files package so we can work with csv files
import DataFiles

########################################################################
############## GET ALL OF THE FIELDS THAT WERE RE-LABELED ##############
########################################################################

# Identify all sub-directories containing the cell labelings performed
# by the various researchers
RALabelDirs = ImageFiles.findSubDirs(cellLabelDir)

# One of these sub-directories will be the location of the re-labelings.
# Identify this directory
reLabelDir = [RALabelDir for RALabelDir in RALabelDirs if 'Relabeled-By-' in RALabelDir]
reLabelDir = os.path.join(cellLabelDir,reLabelDir[0])
del RALabelDir, RALabelDirs

# Store the initials of the researcher who re-labeled the fields of view
reLabelRA = re.findall('Relabeled-By-(.+)',reLabelDir)[0]

# Within the re-labeling directory, you will find an roi file containing
# our true field of view boundary. Locate this file and open it.
fovBoundaryPath = ImageFiles.findImgsInDir(reLabelDir,
                                           '.roi','FieldBoundary')
fovBoundary = ROITools.openROIFile(fovBoundaryPath)

# Within the directory containing the re-done cell labelings there will
# be more sub-directories
labelSubDirs = ImageFiles.findSubDirs(os.path.join(reLabelDir))

# Identify the sub-directory that contains the unlabeled image files.
# These files will be soft links pointing to the folder of the original
# labeler.
unlabeledFieldDir = [labelSubDir for labelSubDir in labelSubDirs if '_Unlabeled_Fields' in labelSubDir]
unlabeledFieldDir = unlabeledFieldDir[0]
del labelSubDir, labelSubDirs

# Generate a list of all unlabeled fields of view paths that were
# re-labeled
relabeledFields = ImageFiles.findImgsInDir(os.path.join(reLabelDir,
                                                        unlabeledFieldDir))

########################################################################
###### COMPARE THE ORIGINAL CELL LABELINGS WITH THE RE-DONE LABELS #####
########################################################################

# Start a dictionary that will store all of the reproducibility metrics
# for each field of view
reproQuants = {'Rater1': [],
               'DC': [],
               'JI': [],
               'Field_of_View_Number': []}

# Start a counter for the total number of fields rated twice
FoV2xsRated = 0

# Loop across all relabeled fields of view
for f in range(len(relabeledFields)):

    ####################################################################
    ######## LOCATE THE ORIGINAL AND RE-DONE CELL LABELING FILES #######
    ####################################################################

    # Store the path to the re-labeled field of view we are currently
    # working on
    relabeledField = relabeledFields[f]

    # Get the field of view number for this field and store in
    # dictionary
    nFoV = ImageFiles.getFieldNumber(relabeledField)

    # Find the re-labeled DAPI segmentation image and field
    # quantification csv file for this field of view
    reLabelSegFile = ImageFiles.findImgsInDir(os.path.join(reLabelDir,
                                                           '*_Segmentations'),
                                              None,
                                              '.+-Segmentation_Field-{}_.*'.format(nFoV))
    # Check to make sure that we were able to locate this segmentation
    if not len(reLabelSegFile) > 0:
        # Move to the next field of view
        continue
    reLabelSeg = ImagePlus(reLabelSegFile)
    reLabelCsv = ImageFiles.findImgsInDir(os.path.join(reLabelDir,
                                                       'Quantifications_By_Field'),
                                          '.csv',
                                          'Field-Quantifications_Field-{}_.*csv'.format(nFoV))
    reLabelQuants = DataFiles.csv2dict(reLabelCsv)

    # We can use the symbolic link stored under the path to the re-
    # labeled field of view to determine the location of the original
    # labeling of this field
    origLabelDir = os.path.dirname(os.path.dirname(os.readlink(relabeledField)))

    # Convert this directory from a relative path to an absolute path
    origLabelDir = os.path.join(cellLabelDir,
                                origLabelDir[origLabelDir.rindex(os.path.sep)+1:])

    # Find the original DAPI segmentation and field quantification csv
    # file for this field of view
    origLabelSegFile = ImageFiles.findImgsInDir(os.path.join(origLabelDir,
                                                             '*_Segmentations'),
                                                None,
                                                '.+-Segmentation_Field-{}_.*'.format(nFoV))
    # Check to make sure that we were able to locate the original
    # segmentation file
    if not len(origLabelSegFile) > 0:
        # Move to the next field of view
        continue
    origLabelSeg = ImagePlus(origLabelSegFile)
    origLabelCsv = ImageFiles.findImgsInDir(os.path.join(origLabelDir,
                                                         'Quantifications_By_Field'),
                                            None,
                                            'Field-Quantifications_Field-{}_.*csv'.format(nFoV))
    origLabelQuants = DataFiles.csv2dict(origLabelCsv)

    # Add this field of view number to our data set
    reproQuants['Field_of_View_Number'].append(nFoV)

    # The initials for the original rater will be stored in the name of
    # this directory
    reproQuants['Rater1'].append(re.match('.+Researcher-(.+)',
                                          origLabelDir).group(1))

    ####################################################################
    #### REPORT THE REPRODUCIBILITY FOR LABELING THIS FIELD OF VIEW ####
    ####################################################################

    # Get the dice coefficient and jaccard index from comparing our two
    # segmentations
    [DC,JI] = ROITools.getDC_JI(origLabelSeg,reLabelSeg,fovBoundary)

    # Add the dice coefficient and jaccard index to our data set
    reproQuants['DC'].append(DC)
    reproQuants['JI'].append(JI)

    # Get a list of all the unique column names from the spreadsheets
    csvColNames = list(set(origLabelQuants.keys() + reLabelQuants.keys() + reproQuants.keys()))

    # Search for the column names that report the raw number of cells
    # for each cell type
    nCellCols = list(set([re.match('^((?:Total_)?N_[^_]*)(?:_Rater1)?$',col).group(1) for col in csvColNames if re.search('^(?:Total_)?N_[^_]*(?:_Rater1)?$',col)]))

    # Loop across all of these csv column names
    for col in nCellCols:

        # Check to see if this column is already present in our
        # reproducibility quants directory
        if not reproQuants.has_key('{}_Rater1'.format(col)):

            # If the column is currently not present in the data set,
            # add the column with 0 for all fields. In other words, no
            # cells of this cell type were labeled in any other fields
            reproQuants['{}_Rater1'.format(col)] = [0] * FoV2xsRated
            reproQuants['{}_Rater2'.format(col)] = [0] * FoV2xsRated

        # Check to see if the column name is present in the original
        # rater's data set
        if origLabelQuants.has_key(col):

            # Add the number of cells of this cell type counted by the
            # first rater to our data set
            reproQuants['{}_Rater1'.format(col)].append(int(origLabelQuants[col][0]))

        # Otherwise...
        else:

            # ... no cells of this cell type were counted by this rater
            reproQuants['{}_Rater1'.format(col)].append(0)

        # Repeat the above for the second rater
        if reLabelQuants.has_key(col):
            reproQuants['{}_Rater2'.format(col)].append(int(reLabelQuants[col][0]))
        else:
            reproQuants['{}_Rater2'.format(col)].append(0)

    # Increase our counter for the number of fields of view that were
    # rated twice
    FoV2xsRated += 1

# Add in the initials of the first rater
reproQuants['Rater2'] = [reLabelRA]*FoV2xsRated
