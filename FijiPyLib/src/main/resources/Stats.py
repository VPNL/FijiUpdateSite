'''
Stats Module

Contains functions for running statistics on our data

    ttest(m1,m2,v1,v2,n1,n2)

        - Computes the t-statistics for a two sample t-test without
          assuming equal variances of the two data sets

    zScoreData(data)

        - Z-scores a list of data

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Import square root from math
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
