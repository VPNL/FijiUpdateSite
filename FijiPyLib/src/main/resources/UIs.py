'''
UIs Module

Contains functions to generate UIs used by our plugins

    whichChoiceUI(title,choiceName,choices)

        - Creates a UI that will ask a user to choose between a list of
          options

    checkBoxUI(title,choices)

        - Creates a UI that will ask the user to check off which choices
          they would like

    textFieldsUI(title,textFieldNames,defaultEntries)

        - Creates a UI that will ask the user to fill out some number of
          text fields

'''

########################################################################
########################### IMPORT PACKAGES ############################
########################################################################

# Import generic dialog so we can make quick and dirty UI's
from ij.gui import GenericDialog

# Import packages from javax.swing so we can make UI elements like text
# fields and buttons
from javax.swing import JTextField,DefaultListModel,JList,ListSelectionModel,JScrollPane,DropMode,BorderFactory,JPanel,JLabel,JFrame,JButton

# Import java packages to allow us to specify dimensions and make
# borders and grids
from java.awt import Dimension,BorderLayout,GridLayout

# Import action listener so we can listen for actions like button
# presses
from java.awt.event import ActionListener

# Import thread so that we can wait until a user presses a button
from java.lang import Thread

# Import izip so we can loop across multiple lists
from itertools import izip

########################################################################
############################ whichChoiceUI #############################
########################################################################

# Define a function that can be used to create UIs to ask user to make
# a choice between options
def whichChoiceUI(title,choiceName,choices):
    '''
    Creates a UI that will ask a user to choose between a list of
    options

    whichChoiceUI(title,choiceName,choices)

        - title (String): The title of the UI that will appear at the
                          top of the popup window

        - choiceName (String or List): Name(s) for the choices you are asking
                                       the user to make (e.g. 'Field of view
                                       size'). These will appear to the left of
                                       a drop down list of choices.

        - choices (List): List of the different choices the user can
                          make. The default choice will be the first in
                          the list.

    OUTPUT the choice that the user made

    AR Oct 2021
    AR May 2023 Can make different choices
    '''

    # Initialize a generic dialog where we can ask the user to make the
    # choice
    UI = GenericDialog(title)

    # Check to see if we are asking the user to make multiple choices
    if isinstance(choiceName,str):

        # Add the choice options to the UI. Set the default choice to the
        # first option in the list
        UI.addChoice(choiceName,choices,choices[0])

        # Display the UI to the user
        UI.showDialog()

        # Return the choice that the user made
        return UI.getNextChoice()

    # If we are asking the user to make multiple choices
    else:

        # Add each choice to the UI
        [UI.addChoice(name,choices,choices[0]) for name in choiceName]

        # Display the UI to the user
        UI.showDialog()

        # Return each choice that the user made as a dictionary
        return {name:UI.getNextChoice() for name in choiceName}

########################################################################
############################## checkBoxUI ##############################
########################################################################

# Define a function that will generate a UI displaying check boxes next
# to choices for the user to decide
def checkBoxUI(title,choices):
    '''
    Creates a UI that will ask the user to check off which choices they
    would like

    checkBoxUI(title,choices)

        - title (String): The title of the UI that will appear at the
                          top of the popup window

        - choices (List): List of the different choices the user can
                          make. The default choice will be the first in
                          the list.

    OUTPUT a list of all choices that were selected by the user in the
           checkbox UI. If no options were selected, returns an empty
           list.

    AR Oct 2021
    '''

    # Initialize a generic dialog where we can ask the user to make the
    # choices
    UI = GenericDialog(title)

    # Add check boxes for all choices possible for the user. Set default
    # to unchecked. The first two arguments setup the number of rows
    # and columns in the check box group, respectively.
    UI.addCheckboxGroup(len(choices),2,choices,[False]*len(choices))

    # Display the UI
    UI.showDialog()

    # Return all choices that were checked off by the user
    return [choice for choice in choices if UI.getNextBoolean()]

########################################################################
############################# textFieldsUI #############################
########################################################################

# Write a UI to ask a user to fill out text fields
def textFieldsUI(title,textFieldNames,defaultEntries):
    '''
    Creates a UI that will ask the user to fill out some number of text
    fields

    textFieldsUI(title,textFieldNames,defaultEntries)

        - title (String): The title you want to give for this UI

        - textFieldNames (List of Strings): Labels you want to give for
                                            each text field

        - defaultEntries (List of Strings): Default text entries for
                                            each text field

    OUTPUT List of strings containing the text entries from the user

    AR Dec 2021
    '''

    # Create the user interface, specifying the title
    UI = GenericDialog(title)

    # Add a text field for each text field name and default entry pair
    [UI.addStringField(name,default,10) for name, default in izip(textFieldNames,defaultEntries)]

    # Display the UI
    UI.showDialog()

    # Return a list of the text the user entered
    return [UI.getNextString() for i in range(len(textFieldNames))]
