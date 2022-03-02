'''
Stats Module

Contains functions for running statistics on our data

    ttest(m1,m2,v1,v2,n1,n2)

        - Computes the t-statistics for a two sample t-test without
          assuming equal variances of the two data sets

    zScoreData(data)

        - Z-scores a list of data

    distanceMatrix(x,y)

        - Computes the distance between every x and y coordinate and
          organizes these distances into a matrix

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Import square root and distance from math
from math import sqrt

# Import java's summary statistics package so we can compute means and
# standard deviations to compute z-scores
from org.apache.commons.math3.stat.descriptive import DescriptiveStatistics as DSS

########################################################################
################################# ttest ################################
########################################################################

# Define a function to run two sample t-tests
def ttest(m1,m2,v1,v2,n1,n2):
    '''
    Computes the t-statistics for a two sample t-test without assuming
    equal variances of the two data sets

    ttest(m1,m2,v1,v2,n1,n2)

        - m1 (float): first sample mean

        - m2 (float): second sample mean

        - v1 (float): first sample variance

        - v2 (float): second sample variance

        - n1 (int): first sample n

        - n2 (int): second sample n

    OUTPUT t-statistic as float

    AR Nov 2021
    '''

    # Return the t-statistic for this test
    return (m1 - m2) / sqrt((v1**2/n1) + (v2**2/n2))

########################################################################
############################## zScoreData ##############################
########################################################################

# Write a function to z-score a list of data
def zScoreData(data):
    '''
    Z-scores a list of data

    zScoreData(data):

        - data (List of Floats): data you want to z-score

    OUTPUT list of z-scored data points

    AR Feb 2022
    '''

    # Initialize a descriptive statistics object so we can compute the
    # average and standard deviation of the sample
    stats = DSS(data)

    # Store the average and standard deviation of the data
    avg = stats.getMean()
    std = stats.getStandardDeviation()
    del stats

    # Return the z-scored list of data
    return [(value - avg)/std for value in data]

########################################################################
############################ distanceMatrix ############################
########################################################################

# Compute the distance between all points in a list
def distanceMatrix(x,y):
    '''
    Computes the distance between every x and y coordinate and organizes
    these distances into a matrix

    distanceMatrix(x,y)

        - x (List of floats): X coordinates of all points in our data
                              set

        - y (List of floats): Y coordinates of all points in our data
                              set

    OUTPUT List of lists of floats representing the distance between all
           points in our data set.

    AR Mar 2022
    '''

    # Store the number of points in the data set
    nPts = len(x)

    # Initialize a list of lists that will store the distances between
    # all points
    distMat = []

    # Loop across all points in our data set, except the last point
    for p in range(nPts-1):

        # Generate a list that will store the distance from this point p
        # to all other sequential points
        distList = [0] * nPts

        # Loop across all points in our data set, starting at the point
        # after p
        for q in range(p+1,nPts):

            # Compute the distance from point p to q and add it to our
            # list of distances
            distList[q] = sqrt((x[p] - x[q])**2 + (y[p] - y[q])**2)

        # Add our list of distances to the distance matrix
        distMat.append(distList)

    # Add a final column with only zeros to the end of the distance
    # matrix
    distMat.append([0] * nPts)

    # Mirror the matrix across the diagonal
    for i in range(nPts):
        for j in range(i+1):
            distMat[i][j] = distMat[j][i]

    # Return the final matrix
    return distMat
