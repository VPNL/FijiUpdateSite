'''
ImageFiles Module

This module contains tools to work easily with image files.

    findImgsInDir(dirPath,fileType=None,searchPhrase=None)

        - Looks inside a directory for files (like images) of a specific
          file type and contain an optional key phrase in the file name.

    findSubDirs(searchPath)

        - Returns all sub directories directly under the folder
          indicated by the user

    makedir(dir2make)

        - Creates a new desired folder

    makeSoftLink(file2Link,linkPath)

        - Creates a softlink for a file

    getFieldNumber(fieldName)

        - Returns the number of this field of view

    getMetadata(imp)

        - Reads the metadata for an image file

    saveCompressedImg(img,path)

        - Saves an image with data compression

    openVirtualStack(path)

        - Opens image file as a virtual stack

'''

########################################################################
############################ IMPORT PACKAGES ###########################
########################################################################

# Import glob so we can list out the contents of a directory, avoiding
# hidden files
import glob

# Import os so we can join file path elements, and check to see if
# something is a file or directory
import os

# Import regular expressions so we can search strings for specific
# information
import re

# Import bio-formats image reader and MetadataTools so we can work with
# image metadata
from loci.formats import CoreMetadata, MetadataTools

# Import Hashtable from java so we can create metadata maps
from java.util import Hashtable

# Import IJ so we can figure out the ImageJ version
from ij import IJ

# Import length from bio formats
from ome.units.quantity import Length

# Import bio formats' units class
from ome.units import UNITS

# Import bio formats' positive float class
from ome.xml.model.primitives import PositiveFloat

# Import bio-format's Tiff writer
from loci.formats.out import TiffWriter

# Import some image tools from bio-formats so we can convert ImagePlus
# images into something readable by bio-formats
from loci.formats.gui import AWTImageTools as tools

########################################################################
############################ findImgsInDir #############################
########################################################################

# Define function to find image files within a directory
def findImgsInDir(dirPath,fileType=None,searchPhrase=None,searchSubDirs=False):
    '''
    Looks inside a directory for files (like images) of an optional file
    type that contain an optional key phrase in the file name.

    findImgsInDir(dirPath,fileType='tif',searchPhrase=None)

        - dirPath (String): Path to directory within which you would
                            like to search for your files

        - fileType (String): File type for the files you are trying to
                             locate, optional (default = None)

        - searchPhrase (String): Regular expression that is contained
                                 within the file name of the files you
                                 are trying to locate, optional
                                 (default = None)

        - searchSubDirs (Boolean): Do you want to search sub-folders
                                   recursively? (default = False, don't
                                   search subfolders)

    OUTPUT

        - files (List of Strings): Paths to all files in directory that
                                   match our desired file type and
                                   search phrase

    AR Oct 2021
    AR Jan 2022: Changed searchPhrase to a regular expression
    AR Mar 2022: Added option to search sub folders
    '''

    # If dirPath was provided in unicode, convert to String
    if isinstance(dirPath,unicode):
        dirPath = str(dirPath)

    # Define a function to check the file type of a file
    def is_file_type(file_path):
        '''
        Check to see if a given file has the correct file type

        is_file_type(file)

            - file_path (String): Path to file that needs the file type
                                  checked

        OUTPUT True if file is of specified our desired file type

        AR 10/21
        '''

        # Check to make sure file types were specified
        if fileType is None:

            # If no file types were specified, all files are fair game
            return True

        else:

            # Check to see if the image file name ends with the
            # specified file type
            if file_path.endswith(fileType):
                return True
            else:
                return False

    # Define a function to check to see if a file name contains our
    # desired key phrase
    def has_search_phrase(file_path):
        '''
        Check to see if a file contains our desired search phrase

        has_search_phrase(file_path)

            - file_path (String): Path to file that needs the file type
                                  checked

        OUTPUT True if file contains our key search phrase

        AR 10/21
        '''

        # Check to see if we have a desired search phrase
        if searchPhrase is None:

            # If there is no search phrase to look for, all files are
            # fine
            return True

        else:

            # Make a regular expression out of the search phrase
            regexp = re.compile(searchPhrase)

            # Check to see if the search phrase is present in the image
            # file name
            if regexp.search(file_path) is None:
                return False
            else:
                return True

    # Initialize a list storing all of the files in our directory of the
    # correct file type and that contain our desired key phrase
    files2return = []

    # If we are searching through sub-directories ...
    if searchSubDirs:

        # Us os.walk to loop across all files in the input directory and
        # its sub directories
        for subDir, _, files in os.walk(dirPath):

            # Loop across all files
            for file_name in files:

                # Concatenate the directory's path with each file name
                full_path = os.path.join(subDir,file_name)

                # Check the file type
                if is_file_type(file_name):

                    # Check to see if the file's path contains our
                    # desired key phrase
                    if has_search_phrase(full_path):

                        # If this file passes these checks, we should
                        # return it
                        files2return.append(full_path)

    else:

        # Use os.listdir to list out the contents of our search directory
        for file_name in glob.glob(os.path.join(dirPath,'*')):

            # Concatenate the directory's path with each file name
            full_path = os.path.join(dirPath,file_name)

            # Check to make sure this content is a file rather than a
            # directory
            if os.path.isfile(full_path) or os.path.islink(full_path):

                # Check the file type
                if is_file_type(file_name):

                    # Check to see if the file contains our desired key
                    # phrase
                    if has_search_phrase(file_name):

                        # If this file passes these checks, we should return
                        # it
                        files2return.append(full_path)

    # Check to see if there was only one file to return
    if len(files2return) == 1:

        # Return just that one file as a string instead of list
        return files2return[0]

    # Otherwise, if there are multiple files to return, just return full
    # list
    return files2return

########################################################################
############################## findSubDirs #############################
########################################################################

# Define a function that will return all sub directories under a path
def findSubDirs(searchPath):
    '''
    Returns all sub directories directly under the folder indicated by
    the user

    findSubDirs(searchPath)

        - searchPath (String): Path to folder under which you would like
                               to find sub directories

    OUTPUT list of strings giving the names of all sub directories under
           searchPath

    AR Oct 2021
    '''

    # Use os.listdir to get all contents under searchPath, and check to
    # see what are subdirectories
    subdirs = [dir for dir in os.listdir(searchPath) if os.path.isdir(os.path.join(searchPath,dir))]

    # If there was more than one sub directory...
    if len(subdirs) > 1:

        # ... return the whole list
        return subdirs

    # If there was only one sub directory ...
    else:

        # ... return that sub directory
        return subdirs[0]

########################################################################
################################ makedir ###############################
########################################################################

# Define a function that will make new directories
def makedir(dir2make):
    '''
    Creates a new desired folder

    makedir(dir2make)

        - dir2make (String): Path to the location of the new directory
                             you want to make

    Will first check to see if the directory you are trying to make
    already exists. It it doesn't already exist, this function will make
    the folder.

    AR Oct 2021
    '''

    # Check to see if the folder already exists
    if not os.path.exists(dir2make):

        # Make the folder if it doesn't already exist
        os.makedirs(dir2make)

########################################################################
############################# makeSoftLink #############################
########################################################################

# Define a function for making soft links
def makeSoftLink(file2Link,linkPath):
    '''
    Creates a softlink for a file

    makeSoftLink(file2Link,linkPath)

        - file2Link (String): Path to the file you want to make a
                              softlink to

        - linkPath (String): File path to where you want to make your
                             soft link

    AR Oct 2021
    '''

    # Store the directory where the link will be saved
    linkDir = os.path.dirname(linkPath)

    # Change the current working directory to where we want to make the
    # soft link
    os.chdir(linkDir)

    # Store the relative path from where the file to be linked is
    # located to where we want to make the soft link
    linkRelPath = os.path.relpath(file2Link,linkDir)

    # Create the softlink
    os.symlink(linkRelPath,linkPath)

########################################################################
############################ getFieldNumber ############################
########################################################################

# Define a function to get the field of view number
def getFieldNumber(fieldName):
    '''
    Returns the number of this field of view

    getFieldNumber(fieldName)

        - fieldName (String): File name of the field of view

    OUTPUT the number of this field of view as an integer

    AR Dec 2021
    AR Feb 2022: Updated since we're no longer numbering fields by row
                 or column
    '''

    # Define a regular expression to identify the row and column numbers
    regex = re.compile('.*Field-(?P<Field_of_View_Number>\d+)_.*')

    # Match the string pattern with our field of view name
    matches = regex.match(str(fieldName))

    # Return the field of view number as an integer
    return int(matches.groupdict()['Field_of_View_Number'])

########################################################################
############################## getMetadata #############################
########################################################################

# Write a function that will get the bio-formats meta data for an image
def getMetadata(imp):
    '''
    Reads the metadata for an image file

    getMetadata(imp)

        - imp (Fiji ImagePlus): Image you want to create metadata for

    OUTPUT MetadataStore object from the bio-formats java library
    containing the metadata for this image

    AR Jan 2022
    '''

    # Initialize an object to store core metadata
    core = CoreMetadata()

    # Store the file info from the ImagePlus
    impFileInfo = imp.getFileInfo()

    # Use the image plus object to extract the image properties to add
    # to the metadata
    core.bitsPerPixel = imp.getBytesPerPixel() * 8 # A byte is a group
                                                   # of 8 bits
    core.dimensionOrder = 'XYZTC'
    core.imageCount = impFileInfo.nImages
    core.littleEndian = impFileInfo.intelByteOrder
    core.pixelType = imp.getBytesPerPixel()
    core.rgb = imp.getBitDepth() == 24 # 24 bit depth for ImagePlus is
                                       # for RGB images
    core.sizeC = imp.getNChannels()
    core.sizeT = imp.getNFrames()
    core.sizeX = imp.getWidth()
    core.sizeY = imp.getHeight()
    core.sizeZ = imp.getNSlices()

    # Create a metadata map for this image
    metaMap = Hashtable()

    # Grab the calibration for this image
    impCalibration = imp.getCalibration()

    # Store the current ImageJ version
    ImageJVersion = IJ.getVersion()

    # Add in metadata for our image into our metadata map
    metaMap.put('ImageLength',imp.getHeight())
    metaMap.put('XResolution',impCalibration.getX(1))
    metaMap.put('ImageJ',ImageJVersion[ImageJVersion.index('/')+1:])
    metaMap.put('YResolution',impCalibration.getY(1))
    metaMap.put('ResolutionUnit',impCalibration.getUnit())
    metaMap.put('Unit',impCalibration.getUnit())
    metaMap.put('NumberOfChannels',imp.getNChannels())
    metaMap.put('BitsPerSample',imp.getBytesPerPixel() * 8)
    metaMap.put('ImageWidth',imp.getWidth())
    metaMap.put('SamplesPerPixel',impFileInfo.samplesPerPixel)

    # Add the metadata map to the core metadata
    core.seriesMetadata = metaMap

    # Initialize an OME-XML metadata storage object
    meta = MetadataTools.createOMEXMLMetadata()

    # Populate this OME-XML metadata storage using our core metadata
    MetadataTools.populateMetadata(meta,0,imp.getTitle(),core)

    # Add the resolution to the image metadata
    # TODO: Don't hard code image resolution
    meta.setPixelsPhysicalSizeX(Length(impCalibration.getX(1),UNITS.MICROMETER),0)
    meta.setPixelsPhysicalSizeY(Length(impCalibration.getY(1),UNITS.MICROMETER),0)
    meta.setPixelsPhysicalSizeZ(Length(impCalibration.getZ(1),UNITS.MICROMETER),0)


    # Return the metadata
    return meta

########################################################################
########################### saveCompressedImg ##########################
########################################################################

# Write a function that will save an image with compression
def saveCompressedImg(img,metaData,outFile):
    '''
    Saves an image with data compression

    saveCompressedImg(img,path)

        - img (ImagePlus): Image you want to saved

        - metaData (Bio-Formats MetadataStore): Metadata for the image
                                                you are saving

        - outFile (String): File path to where you want to save the image

    AR Jan 2022
    '''

    # Initialize a bio-formats image writer object
    writer = TiffWriter()

    # Add the metadata to this writer
    writer.setMetadataRetrieve(metaData)

    # Instruct the writer to save the image with compression
    writer.setCompression("zlib")

    # Set the file location to write to
    writer.setId(outFile)

    # loop across all planes of the image
    for p in range(img.getNSlices()):

        # Set the current z-slice of the image
        img.setSliceWithoutUpdate(p+1)

        # Crop the current z-slice of the image
        curSlice = img.crop()

        # Convert this plane into a java buffered image
        bufrdimg = curSlice.getBufferedImage()

        # Convert the buffered image into a bytes array
        plane = tools.getBytes(bufrdimg)

        # Save the bytes from this plane to the file
        writer.saveBytes(p,plane[0])

    # Close the writer object
    writer.close()

########################################################################
########################### openVirtualStack ###########################
########################################################################

# Define a function to open image files as virtual stacks to save memory
def openVirtualStack(path):
    '''
    Opens image file as a virtual stack

    openVirtualStack(path)

        - path (String): File path to image you want to openVirtualStack

    OUTPUT ImagePlus object containing the virtual stack

    AR Feb 2023
    '''

    # Open the image using bio-formats
    IJ.run("Bio-Formats",
           'open={} color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT use_virtual_stack'.format(path));

    # Grab the image plus object
    imp = IJ.getImage()

    # Hide the image plus object
    imp.hide()

    # Return the resulting image plus object
    return imp
