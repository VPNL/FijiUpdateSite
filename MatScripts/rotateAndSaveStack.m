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

% Copy the image description as well as the x and y resolution
imgDescription = imgInfo.ImageDescription;
imgResolution = [imgInfo.XResolution,imgInfo.YResolution];
clear imgInfo

% Read the image we want to rotate 
img = imread(imgFile2Rotate);

% Rotate our image 
rotatedImg = imrotate(img,-rotAngle);

% Save the final rotated image, overwriting the existing image file 
imwrite(rotatedImg,imgFile2Rotate,'Compression','deflate','Description', ...
        imgDescription,'Resolution',imgResolution)

end