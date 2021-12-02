'''
DataFiles Module

This module contains functions for reading, writing and working with
data files

    dict2csv(dataDict,outPath)

        - Saves a python dictionary out to a csv file

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
