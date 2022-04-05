'''
DataFiles Module

This module contains functions for reading, writing and working with
data files

    dict2csv(dataDict,outPath)

        - Saves a python dictionary out to a csv file

    csv2dict(csvPath)

        - Reads a csv file to a python dictionary

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
