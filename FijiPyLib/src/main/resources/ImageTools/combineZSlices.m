function combineZSlices(separateSliceChannelDir,needsRotation,bestChannel)
% COMBINEZSLICES will combine z slices from a channel that have been
% separated by the Separate_Slices-Channels ImageJ macros that is part of
% the Paredes-GrillSpectorLabs update site.
%
%   combineZSlices(separateSliceChannelDir,needsRotation)
%
%       - separateSliceChannelDir (String): Path to the folder produced by
%                                           the Separate_Slices-Channels
%                                           plugin containing separate tiff
%                                           images from each channel and
%                                           z-slice
%
%       - needsRotation (Boolean): True if the image needs to be rotated
%                                  and cropped. Default = True
%
%       - bestChannel (Num): Channel of the image that has the largest
%                            signal. This channel will be used to define
%                            the boundaries of the image to crop after
%                            rotation. Defaults to first channel.
%
%   Function will save final z-stacks for each image channel as separate
%   tiff images in the directory above the separateSliceChannelDir, where
%   the larger composite image file you get from the microscope will
%   reside.
%
%   AR Dec 2021

% Check to see if needsRotation was provided
if nargin < 2
    
    % Set a default value for needsRotation
    needsRotation = true;

end

% Check to see if bestChannel was provided
if nargin < 3

    % Set default value for bestChannel 
    bestChannel = 1;

end

% Define a function that will get all of the files within a directory
function files = filesInDir(directory)
% FILESINDIR will list out all of the files within a directory
%
%   files = filesInDir(directory)
%
%       directory (String): Path to the directory within which you want all
%                           of the files
%
%       files (Cell Array of Strings): File names for all files within the
%                                      directory
%
% AR Dec 2021

% Get all of the files within the directory
files = dir(directory);

% Exclude any directories from this list of files 
files = files(~[files.isdir]);

% Transform files into a cell array 
files = {files.name};

end

% Store all of the image files found within the folder made by our macros
% script
imgFiles = filesInDir(separateSliceChannelDir);

% Get information of the first image 
imgInfo = imfinfo(fullfile(separateSliceChannelDir,imgFiles{1}));

% Copy the image description as well as the x and y resolution
imgDescription = imgInfo.ImageDescription;
imgResolution = [imgInfo.XResolution,imgInfo.YResolution];
clear imgInfo

% Define a function that will identify the channel and z-slice numbers of
% an image file
function [channel,zSlice] = getChannelSlice(fileName)
% GETCHANNELSLICE will return the channel and z-slice number from an image
% file name
%
%   [channel,zSlice] = getChannelSlice(fileName)
%
%       - fileName (String): Name of the image file that you want the slice
%                            and channel number from
%
%       - channel (Double): Channel number of this file 
%
%       - zSlice (Double): z-slice of this file 
%
% AR Dec 2021

% Define a regular expression that will pick up the channel and slice
% number 
expr = 'c(?<channel>\d+)z(?<slice>\d+)_';

% Apply the regular expression to the file name
matchCell = regexp(fileName,expr,'tokens');

% The channel and z-slice number can be extracted from the cell array
% produced by regexp 
channel = str2double(matchCell{1}{1});
zSlice = str2double(matchCell{1}{2});

end

% Extract all of the channel and z-slice numbers from all of the
% discoverable image files 
[channels,slices] = cellfun(@getChannelSlice,imgFiles);

% Store only the unique channels and slices without repeats 
channels = unique(channels);
slices = unique(slices);

% Store the general name of the image file without the channel and slice
% information
baseFileName = extractAfter(imgFiles{1}, ...
                            regexpPattern('c(?<channel>\d+)z(?<slice>\d+)_'));
clear imgFiles

% Check to see if we want to rotate and crop the images
if needsRotation

    % Store the image file name for the first channel middle slice. This 
    % serve as a reference image to compute the rotation and the amount of
    % cropping
    refImgFileName = append('c',num2str(bestChannel),'z', ...
                            num2str(round(max(slices)/2)),'_', ...
                            baseFileName);
    clear bestChannel

    % Open up this reference image 
    refImg = imread(fullfile(separateSliceChannelDir,refImgFileName));
    clear refImgFileName

    % We will want to rotate the image such that the diagonal from the top
    % left corner to the bottom right corner of the image becomes vertical.
    % Compute the angle of rotation below using the image dimensions and
    % convert this angle from radians to degrees.
    rotAngle = rad2deg(atan(size(refImg,2)/size(refImg,1)));

    % We'll want to save this rotation angle to a text file so we can keep
    % track. Get our base file name without the image type extension (e.g.
    % 'tif')
    [~,baseTextFileName,~] = fileparts(baseFileName);

    % Open the text file where we will print out the rotation angle
    rotTextFID = fopen(fullfile(separateSliceChannelDir,'..', ...
                                append('RotationInDegrees_', ...
                                       baseTextFileName,'.txt')),'wt');
    clear baseTextFileName

    % Print the rotation angle to the text file 
    fprintf(rotTextFID,num2str(rotAngle));

    % Close the text file
    fclose(rotTextFID);

    % Rotate our reference image
    rotatedRef = imrotate(refImg,rotAngle);
    clear refImg;

    % Identify the rows and columns that contain at least one nonzero pixel
    % intensity
    rows2keep = find(any(rotatedRef,2));
    cols2keep = find(any(rotatedRef,1));
    clear rotatedRef

end

% Loop across all channels that were present in the composite image 
for c = channels

    % Store the tiff file path that will contain the z-stack for this
    % channel
    filePath4Channel = fullfile(separateSliceChannelDir,'..', ...
                                append('c',num2str(c),'_',baseFileName));
    
    % Loop across all slices for this channel 
    for z = slices

        % Store the file path to the image at this channel and z-slice 
        currFilePath = fullfile(separateSliceChannelDir, ...
                                append('c',num2str(c),'z', num2str(z),'_', ...
                                       baseFileName));

        % Read the image at this file path 
        currImg = imread(currFilePath);
        clear currFilePath

        % Check to see if we want to rotate and crop the image 
        if needsRotation

            % Rotate the image
            currImg = imrotate(currImg,rotAngle);

            % Crop the rotated image 
            currImg = currImg(rows2keep,cols2keep);

        end

        % Append the image at this z-level to our composite z-stack file 
        imwrite(currImg,filePath4Channel,'WriteMode','append', ...
                'Compression','deflate','Description',imgDescription, ...
                'Resolution',imgResolution);
        clear currImg

    end

end

end