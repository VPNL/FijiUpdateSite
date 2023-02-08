function tags = getTiffTagValues(file2Read)
%getTiffTagValues reads a TIFF file and returns a structure array
%containing TIFF tags and their corresponding values for this image
%
%   tags = getTiffTagValues(file2Read)
%
%       - file2Read (String): Path to the image file you want to read
%
%       - tags (Struct): Structure array with different fields for all TIFF
%                        tags stored in the TIFF file with their 
%                        corresponding values
%
% AR Feb 2023

% Open the TIFF file by creating a Tiff object
t = Tiff(file2Read,'r+');

% Store all recognized TIFF tags
tagNames = Tiff.getTagNames();

% Store the read-only TIFF tags
readOnlyTIFFTags = {'StripByteCounts','StripOffsets','TileByteCounts',...
                    'TileOffsets','ImageDepth','NumberOfInks'};

% Remove read-only TIFF tags from our list of recognized TIFF tags
tagNames = setdiff(tagNames,readOnlyTIFFTags);

% Create a new structure array that will store the values of all TIFF tags
% for this image
tags = struct;

% Loop across all recognized TIFF tags
for n = 1:length(tagNames)
    tagName = tagNames{n};
    
    % If the tag is present in our TIFF image, store the corresponding
    % value
    try
        tags.(tagName) = getTag(t,tagName);
    end

end

end