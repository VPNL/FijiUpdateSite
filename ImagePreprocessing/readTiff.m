function [img,img_info] = readTiff(img_file)
% READTIFF Reads a tiff file into a matrix, making sure that all pages of
% multipage tiff tiles are read.
%
%   img = readTiff(img_file)
%
%       img_file: (String) File path to the image you would like to open
%
%       img: (Matrix) Pixel intensities of the image corresponding to
%            img_file
%
%       img_info: (Struct) Information about the graphics file, returned 
%                 as a structure array.

% Get the format information for this image
img_info = imfinfo(img_file);

% Get the size of the image
n = img_info(1).Height;
m = img_info(1).Width;
z = numel(img_info);

% If the tiff file is multipage
if z > 1

    % Initialize a matrix of proper dimensions to store the image
    img = zeros(n,m,z,'uint8');

    % Loop across all pages in the image
    for p = 1:z
    
        % Read the image from this page
        img(:,:,p) = imread(img_file,p);
    
    end

% Otherwise, we can just use imread
else
    
    img = imread(img_file);
    
end

end