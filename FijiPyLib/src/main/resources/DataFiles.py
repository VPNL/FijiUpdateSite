'''
DataFiles Module

This module contains functions for reading, writing and working with
data files

    dict2csv(dataDict,outPath)

        - Saves a python dictionary out to a csv file

    csv2dict(csvPath)

        - Reads a csv file to a python dictionary

    getNElementsInDict(dic)

        - Returns the number of elements in the python dictionary,
          assuming the values of all keys in the dictionary are lists of
          the same length like a pandas data frame

    mergeDataDicts(dicts)

        - Merges a list of python dictionaries

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Import csv so we can read and write csv files
import csv

# Import izip so we can iterate across multiple lists
from itertools import izip

########################################################################
############################### dict2csv ###############################
########################################################################

# Write a function to save a python dictionary to a csv file
def dict2csv(dataDict,outPath):
    '''
    Saves a python dictionary out to a csv file

    dict2csv(dataDict,outPath)

        - dataDict (Python Dictionary): Dictionary containing the data
                                        you want to write to a csv file

        - outPath (String): File path to where you want to save your
                            csv file

    AR Dec 2021
    '''

    # Open the csv file where we will be saving our data
    with open(outPath,'w') as outfile:

        # Initialize a writer object to write the csv file
        writer = csv.writer(outfile)

        # Write all the keys of the dictionary as the column names of
        # the csv file
        writer.writerow(dataDict.keys())

        # Write all of the values from each key in the dictionary as the
        # data in the subsequent rows
        writer.writerows(izip(*dataDict.values()))

        # Close the csv file
        outfile.close()

########################################################################
############################### csv2dict ###############################
########################################################################

# Write a function to read csv files
def csv2dict(csvPath):
    '''
    Reads a csv file to a python dictionary

    csv2dict(csvPath)

        - csvPath (String): File path to the location of the csv file
                            you want to read into a dictionary

    OUTPUTS a python dictionary

    AR April 2022
    '''

    # Open the csv file
    with open(csvPath) as csvFile:

        # Read the csv file row by row
        csvReader = csv.reader(csvFile)

        # Read the first row of the csv file
        for row in csvReader:

            # Store the list of all the column names in the csv file
            cols = row

            # End the loop as we only want to read the first row
            break

        # Initialize a python dictionary that will contain the contents
        # of the csv file
        dict = {}

        # Loop across all of the column names in the csv file
        for key in cols:

            # Initialize a list under this key
            dict[key] = []

    # Re-open the csv file so we can read it with a different package
    with open(csvPath) as csvFile:

        # Use the dict reader to read the csv file row by row
        reader = csv.DictReader(csvFile)

        # Loop across all rows of the csv file
        for row in reader:

            # Loop across all column titles
            for key in row.keys():

                # Append this value to our dictionary
                dict[key].append(row[key])

    # Return the final dictionary
    return dict

########################################################################
########################## getNElementsInDict ##########################
########################################################################

# Write a function that will compute the number of elements in a python
# dictionary
def getNElementsInDict(dic):
    '''
    Returns the number of elements in the python dictionary, assuming
    the values of all keys in the dictionary are lists of the same
    length like a pandas data frame

    getNElementsInDict(dic)

        - dic (Python Diciontary): Dictionary containing data organized
                                   in lists of the same length under
                                   each index key

    OUTPUTS the number of elements in the python dictionary as an
    integer

    AR April 2022
    '''

    # Check to see if the dictionary is empty (would have no keys)
    if len(dic.keys()) > 0:

        # Return the length of the list stored under the first key in
        # the dictionary
        return len(dic[dic.keys()[0]])

    # If the dictionary did not have any keys ...
    else:

        # ... then it also did not have any elements
        return 0

########################################################################
############################ mergeDataDicts ############################
########################################################################

# Write a function that will merge python dictionaries containing data
def mergeDataDicts(dicts):
    '''
    Merges two python dictionaries

    mergeDataDicts(dicts)

        - dicts (List of Python Dictionary): Dictionaries containing our
                                             data. Values of all keys
                                             must be lists of the length
                                             across all keys in each
                                             dictionary.

    OUTPUTS python dictionary containing the merged data

    AR April 2022
    '''

    # Get a list of all the unique keys across the dictionaries
    allKeys = []
    [allKeys.extend(dict.keys()) for dict in dicts]
    keys = list(set(allKeys))

    # Initialize a python dictionary that will contain the merged data
    mergedDict = {}
    for key in keys:
        mergedDict[key] = []

    # Loop across all dictionaries that we want to merge
    for dic in dicts:

        # Get the number of elements in each list stored under the keys
        # of this dictionary
        nElem = getNElementsInDict(dic)

        # Loop across all keys
        for key in keys:

            # Check to see if the key is in the dictionary
            if dic.has_key(key):

                # If the key is in our dictionary, just add the list
                # under this key to our merged dictionary
                mergedDict[key].extend(dic[key])

            # If the key is not in the dictionary ...
            else:

                # ... then we need to fill in the blank data with nans
                mergedDict[key].extend([float('nan')]*nElem)

    # Return the final merged dictionary
    return mergedDict
