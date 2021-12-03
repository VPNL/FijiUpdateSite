function saveTiff(file_name,img,orig_tag_struct)
% SAVETIFF saves a tiff file storing a new image matrix, making sure all of
% the multipage settings are accurate.
%
%   saveTiff(file_name,img)
%
%       file_name: (String) File path to where you want to save your image
%
%       img: (Matrix) Pixel intensities of the image corresponding to
%            img_file
%
%       orig_tag_struct: (struct) Multiple tags, specified as a structure 
%                        containing TIFF tag names and their corresponding 
%                        values.
%{
% Create a new tiff object
tif_obj = Tiff(file_name,'w');

% Set the tags for this new tiff object
%{
tag_struct = struct('Compression',...
                    Tiff.Compression.(tag_struct(1).Compression),'ImageWidth',...
                    size(img,1),'ImageLength',size(img,2),'BitsPerSample',8,...
                    'SamplesPerPixel',size(img,3),'PlanarConfiguration',...
                    Tiff.PlanarConfiguration.(tag_struct(1).PlanarConfiguration),'Photometric',Tiff.Photometric.MinIsBlack,'XResolution',...
                    tag_struct(1).XResolution,'YResolution',...
                    tag_struct(1).YResolution,'ResolutionUnit',...
                    Tiff.ResolutionUnit.(tag_struct(1).ResolutionUnit));}
%}
tag_struct = struct('ImageLength',size(img,2),'Photometric',...
                    Tiff.Photometric.MinIsBlack,'PlanarConfiguration',...
                    Tiff.PlanarConfiguration.(orig_tag_struct(1).PlanarConfiguration),...
                    'BitsPerSample',8,'SamplesPerPixel',size(img,3),'ImageWidth',...
                    size(img,1),'Compression',Tiff.Compression.None);
                
setTag(tif_obj,tag_struct);

% Write out the tile matrix to the tif file
write(tif_obj,uint8(img));
%}
for z = 1:size(img,3)
    imwrite(uint8(img(:,:,z)),file_name,'WriteMode','append','Compression','none');
end
end