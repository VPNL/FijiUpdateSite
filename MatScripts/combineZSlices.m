function combineZSlices(separateSliceChannelDir,needsRotation,bestChannel)
% COMBINEZSLICES will combine z slices from a channel that have been
% separated by the Separate_Slices-Channels ImageJ macros that is part of
% the Paredes-GrillSpectorLabs update site.
%
%   combineZSlices(separateSliceChannelDir,needsRotation,bestChannel)
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
%   AR Jan 2022: Changed angle saved to text file to negative to correspond
%   with how the angle will be interpreted in Fiji/ImageJ
%   AR Feb 2022: Moved files in dir function to a separate file, make sure
%                to export rotation angle if 0
%   AR Mar 2022: Fixed angle of rotation. Needed to check to see which
%                direction we should rotate and was over-rotating by a
%                factor of 2.
%   AR Apr 2022: Check to see which direction we direction we should rotate
%                                       by actually trying both
%   AR Jan 2023: Check the dimensions of the image and inspect some pixel
%                values to determine the optical rotation angle

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

% Check to see if needsRotation was provided as a character array
if ischar(needsRotation)

    % Convert needsRotation from a character array to a boolean
    needsRotation = strcmpi(needsRotation,'true');

end

% Check to see if bestChannel was provided as a character array
if ischar(bestChannel)

    % Convert bestChannel to a double
    bestChannel = str2double(bestChannel);

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

    % Store the image file name for the first channel's middle slice. This
    % serve as a reference image to compute the rotation and the amount of
    % cropping
    refImgFileName = append('c',num2str(bestChannel),'z', ...
                            num2str(round(max(slices)/2)),'_', ...
                            baseFileName);
    clear bestChannel

    % Open up this reference image
    refImg = imread(fullfile(separateSliceChannelDir,refImgFileName));
    clear refImgFileName

    % Store the width and height of the reference image
    refImgH = size(refImg,1);
    refImgW = size(refImg,2);

    % Store half of the shorter length
    half = round(min(refImgW,refImgH) / 2);

    % Count the number of non-zero pixel values in the top left and right
    % corners of the image
    topLeftNNZ = nnz(refImg(1:half,1:half));
    topRightNNZ = nnz(refImg(1:half,end-half:end));
    clear half
    
    % If the image is taller than it is wide...
    if refImgH > refImgW

        % ... and the image runs from the top left corner to the bottom
        % right...
        if topLeftNNZ > topRightNNZ
            
            % ... rotate the image clockwise by the arc tangent of the
            % width over the height
            rotAngle = -rad2deg(atan(refImgW/refImgH))/2;
        
        % If the tilescan runs from the bottom left corner to the top
        % right...
        else
            
            % ... rotate the image counter-clockwise
            rotAngle = rad2deg(atan(refImgW/refImgH))/2;

        end
    
    % If the image is wider than it is tall...
    else
        
        % ... and runs from top left to bottom right...
        if topLeftNNZ > topRightNNZ
            
            % ... rotate counter-clockwise by the arc tangent of the height
            % over the width
            rotAngle = rad2deg(atan(refImgH/refImgW))/2;
        
        % If the image runs from the bottom left to the top right...
        else
            
            % ... rotate clockwise
            rotAngle = -rad2deg(atan(refImgH/refImgW))/2;

        end

    end
    
    % We will want to rotate the image such that the diagonal from the top
    % left corner to the bottom right corner of the image becomes vertical.
    % Compute the angle of rotation below using the image dimensions and
    % convert this angle from radians to degrees.
    %rotAngle = rad2deg(atan(refImgW/refImgH));
    clear refImgW refImgH

    % Rotate our reference image one direction
    rotatedRef = imrotate(refImg,rotAngle);

    % Store what rows and columns of the final image we would want to keep
    rows2keep = find(any(rotatedRef,2));
    cols2keep = find(any(rotatedRef,1));

    %{
    % Compute the final area of the image if we would rotate the image this
    % direction
    area2keep1 = sum(any(rotatedRef1,1)) * sum(any(rotatedRef1,2));

    % Rotate our reference image the other direction 
    rotatedRef2 = imrotate(refImg,-rotAngle);
    clear refImg

    % Compute the final area for this rotation 
    area2keep2 = sum(any(rotatedRef2,1)) * sum(any(rotatedRef2,2));

    % Check to see which direction we should rotate the image 
    if area2keep1 < area2keep2

        clear rotatedRef2
        % Identify the rows and columns that contain at least one nonzero 
        % pixel intensity for the image rotated in this direction
        rows2keep = find(any(rotatedRef1,2));
        cols2keep = find(any(rotatedRef1,1));
        clear rotatedRef1

    else

        clear rotatedRef1
        % Indicate that we would like to rotate the image the opposite way 
        rotAngle = -rotAngle;

        % Store which rows and columns to keep 
        rows2keep = find(any(rotatedRef2,2));
        cols2keep = find(any(rotatedRef2,1));
        clear rotatedRef2

    end
    %}

else

    % If we don't need to rotate, the rotation angle is 0
    rotAngle = 0;

end

% We'll want to save this rotation angle to a text file so we can keep
% track. Get our base file name without the image type extension (e.g.
% 'tif')
[~,baseTextFileName,~] = fileparts(baseFileName);

% Open the text file where we will print out the rotation angle
rotTextFID = fopen(fullfile(separateSliceChannelDir,'..', ...
                            append('RotationInDegrees_', ...
                                   baseTextFileName,'.txt')),'wt');
clear baseTextFileName

% Print the rotation angle to the text file. Print as a negative number
% since Fiji/ImageJ interprets angles the opposite as imrotate in
% Matlab
fprintf(rotTextFID,num2str(-rotAngle));

% Close the text file
fclose(rotTextFID);

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

        % Check to see if the image is tall or wide
        if size(currImg,1) > size(currImg,2)

            % If the image is taller than it is wide, we'll need to rotate
            % it by 90 degrees so that it's wider than it is tall
            currImg = rot90(currImg);

        end

        % Append the image at this z-level to our composite z-stack file
        imwrite(currImg,filePath4Channel,'WriteMode','append', ...
                'Compression','deflate','Description',imgDescription, ...
                'Resolution',imgResolution);
        clear currImg

    end

end

end
