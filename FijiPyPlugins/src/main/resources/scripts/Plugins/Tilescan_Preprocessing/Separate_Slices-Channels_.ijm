/*
Separate Slices-CHANNELS

This script will separate a large, virtual stack currently open in Fiji into 
separate tiff images for each individual z-level and channel. These images will
be saved under a folder called "Separate_Slices-Channels" that is a subfolder of
the image you are processing. Each image name will start with c_z_, specifying
the channel and z-level the image comes from.

AR Dec 2021
*/

// Set to batch mode so that new images are hidden
setBatchMode(true);

// Get the number of channels in the currently opened image
max_c = getInfo('SizeC');

// Get the number of z slices in the image
max_z = getInfo('SizeZ');

// Get the file path to the image
img_file_path = getInfo('Location');

// Get the file name without the path
img_file_name = File.getNameWithoutExtension(img_file_path);

// Get the directory where the image is saved
img_dir = File.getDirectory(img_file_path);

// Store the file separation character (last character in img_dir string)
separator = img_dir.charAt(img_dir.length() - 1);

// Create a directory where all individual channels and z-slices will be saved
out_dir = img_dir + 'Separate_Slices-Channels' + separator
File.makeDirectory(out_dir);

// Loop across all channels of the image
for (c=1; c<=max_c; c++) {

	// Loop across all z slices of the image
	for (z=1; z<=max_z; z++) {

		// Duplicate the current channel and slice of the image
		run("Duplicate...", "duplicate channels=" + c + "-" + c + " slices=" + z + "-" + z);

		// Save the image of the current channel and slice as a tif image
		saveAs('tiff',out_dir + 'c' + c + 'z' + z + '_' + img_file_name);

		// Close the image for this slice and channel
		close();

	}

}
