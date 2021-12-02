'''
Stats Module

Contains functions for running statistics on our data

    ttest(m1,m2,v1,v2,n1,n2)

        - Computes the t-statistics for a two sample t-test without
          assuming equal variances of the two data sets

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Import square root from math
from math import sqrt

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
