'''
UIs Module

Contains functions to generate UIs used by our plugins

    whichChoiceUI(title,choiceName,choices)

        - Creates a UI that will ask a user to choose between a list of
          options

    checkBoxUI(title,choices)

        - Creates a UI that will ask the user to check off which choices
          they would like

    orderListUI()
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

        - choiceName (String): A name for the choice you are asking the
                               user to make (e.g. 'Field of view size').
                               This will appear to the left of a drop
                               down list of choices.

        - choices (List): List of the different choices the user can
                          make. The default choice will be the first in
                          the list.

    OUTPUT the choice that the user made

    AR Oct 2021
    '''

    # Initialize a generic dialog where we can ask the user to make the
    # choice
    UI = GenericDialog(title)

    # Add the choice options to the UI. Set the default choice to the
    # first option in the list
    UI.addChoice(choiceName,choices,choices[0])

    # Display the UI to the user
    UI.showDialog()

    # Return the choice that the user made
    return UI.getNextChoice()

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
############################## orderListUI #############################
########################################################################

# Define a function that will display a UI asking the user to order a
# list of options
def orderListUI(list2order,instructions4user,titleOfUI=''):
    '''
    AR Nov 2021
    '''

    # Create a panel that will contain text fields for the user to
    # indicate the desired order of the list
    orderingPanel = JPanel()

    # Create a grid layout for the various text fields and ording labels
    orderingPanel.setLayout(GridLayout(len(list2order),2))

    # Loop across the length of the list that we want to order
    for i in range(len(list2order)):

        # Add a label asking the user to specify the i+1'th element of
        # the list
        orderingPanel.add(JLabel(str(i + 1) + ':'))

        # Add a corresponding text field where the user can specify this
        # list element
        orderingPanel.add(JTextField('',10))

    # Create a boarder around this panel and add in instructions for the
    # user
    orderingPanel.setBorder(BorderFactory.createTitledBorder(instructions4user))

    # Create a list model where we can add all of our list elements
    listModel = DefaultListModel()

    # Loop across all elements of the list
    for element in list2order:

        # Add each element of the list to our list model
        listModel.addElement(element)

    # Create a JList containing our list
    List = JList(listModel)

    # Make sure only one element of the list can be clicked and dragged
    # at a time
    List.setSelectionMode(ListSelectionModel.SINGLE_INTERVAL_SELECTION)

    # Add a scroll pane so we can scroll up and down the list
    scrollPane = JScrollPane(List)

    # Set the dimensions
    scrollPane.setPreferredSize(Dimension(400,100))

    # Make sure that our list is drag enabled
    List.setDragEnabled(True)

    # Create a panel that will store this scroll pane
    optionsPanel = JPanel(BorderLayout())

    # Add our scroll pane to this panel
    optionsPanel.add(scrollPane,BorderLayout.CENTER)

    # Set a boarder around this panel and give it a helpful title
    optionsPanel.setBorder(BorderFactory.createTitledBorder('Drag each element from the list below into the appropriate text field above.'))

    # Create a JFrame object that will have the full UI. Give the UI a
    # title
    frame = JFrame(titleOfUI)

    # Create a class of objects that implements java's ActionListener
    # so we can make buttons that close the JFrame
    class markerOrder(ActionListener):

        # Define a method describing what to do when a button is pressed
        def actionPerformed(self,event):

            # Specify that when the button is pressed, we want to close
            # the JFrame
            frame.dispose()

    # Add a button for the user to indicate when they are done
    # re-ordering the list
    button = JButton('Done')

    # Specify that we want the button to close the JFrame when pressed
    button.addActionListener(markerOrder())

    # Create a JPanel that will contain all of the elements of the UI
    # ordered in a grid
    allPanel = JPanel()

    # Specify that the grid layout of the UI will have 3 rows and 1
    # column
    allPanel.setLayout(GridLayout(3,1))

    # Add the panel containing the text fields where the user indicates
    # the final order of the list
    allPanel.add(orderingPanel)

    # Add the panel containing all of the list elements that need to be
    # sorted by the user
    allPanel.add(optionsPanel)

    # Add the button for the user to indicate that they are done
    # re-ordering the list
    allPanel.add(button)

    # Add this all encompassing panel to our JFrame
    frame.getContentPane().add(allPanel)

    # Make the frame opaque
    frame.getContentPane().setOpaque(True)

    # Pack and display the frame
    frame.pack()
    frame.setVisible(True)

    # Create a while loop that will check to see if the frame is still
    # open
    while True:

        # Check if frame is open
        if frame.isVisible():

            # If the frame is still open ...
            try:

                # Wait a second before checking again
                Thread.sleep(1000)

            # If there was an exception thrown
            except InterruptedException as e:

                # End the while loop
                break

        # If the frame was closed
        else:

            # Finish the while loop
            break

    # Return the list ordered by the user
    return [textField.getText() for textField in orderingPanel.getComponents() if isinstance(textField,JTextField)]
