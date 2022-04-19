function rotateAndSaveStacks(imgFilesDir,rotAngle,channel4Crop)
% ROTATEANDSAVESTACKS Rotates a set of image stacks, crops them, and then
% saves them using a deflation compression
%
%   rotateAndSaveStacks(imgFilesDir,rotAngle,channel4Crop)
%
%       - imgFilesDir (String): File paths to the folder containing the
%                               images you want to rotate
%
%       - rotAngle (Double): Angle that you want to rotate your image in
%                            degrees in a clockwise direction
%
%       - channel4Crop (Int): Which channel would you like to use to
%                             define what rows and columns are croppped
%                             after rotation
%
%   Function will save the final, rotated image stacks, creating new
%   image files with the same file name as our input string, but with the
%   prefix 'Rotated_' added to the beginning
%
%   AR Jan 2022
%   AR Feb 2022 Inputs all image files of all channels so that we can
%               crop after rotating
%   AR Apr 2022 Use max projection to define area to crop

% Convert the rotation angle and channel4Crop from character arrays to the
% correct data type if necessary
if ischar(rotAngle)
    rotAngle = str2double(rotAngle);
end
if ischar(channel4Crop)
    channel4Crop = str2double(channel4Crop);
end

% Get a list of all of the files contained in the input directory
allFiles = filesInDir(imgFilesDir);

% Get a list of all of the separate channels of the image we want to rotate
imgFiles2Rotate = allFiles(~cellfun(@isempty,regexp(allFiles,'c\d+_')));
clear allFiles

% Store the name of the image we want to use to define our cropping
% boundaries
imgFile4Cropping = fullfile(imgFilesDir,imgFiles2Rotate{~cellfun(@isempty, ...
                                                                 regexp(imgFiles2Rotate, ...
                                                                        sprintf('c%d_', ...
                                                                        channel4Crop)))});

% Get the information of the image we want to use to set our cropping
% bounds
imgInfo = imfinfo(imgFile4Cropping);

% Copy the image description, the x and y resolution, and the number of
% z-planes
imgDescription = imgInfo(1).ImageDescription;
imgResolution = [imgInfo(1).XResolution,imgInfo(1).YResolution];
imgNSlices = numel(imgInfo);
clear imgInfo

% Read and rotate the first z-level of the image we want to use to define
% our crop 
rotatedImg4CropDef = imrotate(imread(imgFile4Cropping,1),-rotAngle);

% Loop across all other z levels of the image 
for z = 2:imgNSlices

    % Generate a maximum intensity projection across all z-levels of our
    % image 
    rotatedImg4CropDef = max(cat(3,rotatedImg4CropDef,...
                             imrotate(imread(imgFile4Cropping,z),...
                                      -rotAngle)),[],3);

end
clear imgFile4Cropping

% Store which rows and columns contain actual data rather than blank space
rows2keep = find(any(rotatedImg4CropDef,2));
cols2keep = find(any(rotatedImg4CropDef,1));
clear rotatedImg4CropDef

% Loop across all image files that we want to rotate
for imgFile2Rotate = imgFiles2Rotate

    % Separate the image file path into separate components
    [~,imgFileName,imgFileExt] = fileparts(imgFile2Rotate{1});

    % Store the name of the file we want to save the rotated image to
    rotatedImgFile = fullfile(imgFilesDir,strcat('Rotated_',imgFileName, ...
                                                imgFileExt));
    clear imgFileDir imgFileName imgFileExt

    % Loop across all z-levels of the image
    for z = 1:imgNSlices

        % Read and rotate the current slice of the image
        rotatedImgSlice = imrotate(imread(fullfile(imgFilesDir, ...
                                                   imgFile2Rotate{1}),z), ...
                                   -rotAngle);

        % Crop and save the final rotated image
        imwrite(rotatedImgSlice(rows2keep,cols2keep),rotatedImgFile, ...
                'Compression','deflate', 'Description', imgDescription, ...
                'Resolution',imgResolution, 'WriteMode','append');

    end

end

end
