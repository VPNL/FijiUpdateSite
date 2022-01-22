function rotateAndSaveStack(imgFile2Rotate,rotAngle,xLowBound,xHighBound, ...
                            yLowBound,yHighBound)
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
%   rotateAndSaveStack(__,xLowBound,xHighBound,yLowBound,yHeighBound)
%
%       - xLowBound (Int): Lowest x coordinate you want to include in the
%                          final image after rotation
%
%       - xHighBound (Int): Highest x coordinate you want to include in the
%                           final image after rotation
%
%       - yLowBound (Int): Lowest y coordinate you want to include in the
%                          final image after rotation
%
%       - yHighBound (Int): Highest y coordinate you want to include in the
%                           final image after rotation
%
%   Function will save the final, rotated image stack, overwriting the
%   original image file.
%
%   AR Jan 2022

% Convert all inputs from character arrays to the correct data type
if ischar(rotAngle)
    rotAngle = str2double(rotAngle);
end
if nargin > 2
    if ischar(xLowBound)
        xLowBound = uint8(str2double(xLowBound));
    end
    if ischar(xHighBound)
        xHighBound = uint8(str2double(xHighBound));
    end
    if ischar(yLowBound)
        yLowBound = uint8(str2double(yLowBound));
    end
    if ischar(yHighBound)
        yHighBound = uint8(str2double(yHighBound));
    end
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

% If we defined bounds to crop our image... 
if nargin > 2

    % ... crop the rotated image 
    rotatedImg = rotatedImg(xLowBound:xHighBound,yLowBound:yHighBound);

end

% Save the final rotated image, overwriting the existing image file 
imwrite(rotatedImg,imgFile2Rotate,'Compression','deflate','Description', ...
        imgDescription,'Resolution',imgResolution)

end