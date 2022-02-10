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