function rotateAndSaveStack(imgFile2Rotate,rotAngle)
% ROTATEANDSAVESTACK Rotates an image stack, crops it, and then saves it
% using a deflation compression
%
%   rotateAndSaveStack(imgFile2Rotate,rotAngle)
%
%       - imgFile2Rotate (String): File path to the image you want to
%                                  rotate
%
%       - rotAngle (Double): Angle that you want to rotate your image in
%                            degrees in a clockwise direction
%
%   Function will save the final, rotated image stack, overwriting the
%   original image file.
%
%   AR Jan 2022

% Convert all inputs from character arrays to the correct data type
if ischar(rotAngle)
    rotAngle = str2double(rotAngle);
end

% Get the information of the current image file
imgInfo = imfinfo(imgFile2Rotate);

% Copy the image description, the x and y resolution, and the number of
% z-planes
imgDescription = imgInfo(1).ImageDescription;
imgResolution = [imgInfo(1).XResolution,imgInfo(1).YResolution];
imgNSlices = numel(imgInfo);
clear imgInfo

% Break up the input file name into separate parts 
[imgFileDir,imgFileName,imgFileExt] = fileparts(imgFile2Rotate);

% Store the name of the file we want to save the rotated image to 
rotatedImgFile = fullfile(imgFileDir,strcat('Rotated_',imgFileName, ...
                                            imgFileExt));
clear imgFileDir imgFileName imgFileExt

% Loop across all z-levels of the image 
for z = 1:imgNSlices

    % Read the current slice of the image 
    imgSlice = imread(imgFile2Rotate,z);
    
    % Rotate this image slice
    rotatedImgSlice = imrotate(imgSlice,-rotAngle);

    % Save the final rotated image, overwriting the existing image file 
    imwrite(rotatedImgSlice,rotatedImgFile,'Compression','deflate', ...
            'Description', imgDescription,'Resolution',imgResolution, ...
            'WriteMode','append');

end

end