# Paredes-GrillSpectorLabs Fiji/ImageJ Update Site
This repository contains a collection of several ImageJ scripts that process and analyze tile scan microscope images.

## Installation
To access our plugins directly from your Fiji/ImageJ download, [follow our update site][installationInstructions] using our the URL `https://sites.imagej.net/Paredes-GrillSpectorLabs/`.

## Development
This repository uses [Maven][maven] for versioning and building jar files. To further develop our code
1. Clone this repository using `git clone https://github.com/VPNL/FijiUpdateSite.git`.
2. Edit and add Fiji plugin scripts under `FijiPyPlugins/src/main/resources/scripts/Plugins`. You can use or further develop our Python helper functions and object classes under `FijiUpdateSite/FijiPyLib/src/main/resources`. Additionally, we have some Matlab functions saved under `MatScripts` that can be used or edited for image processing steps.
3. Edit `pom.xml` files to reflect your project information.
4. Run `mvn -Dscijava.app.directory=/path/to/your/ImageJ.app` to build jar files with your code and copy them directly into your ImageJ/Fiji installation.

[installationInstructions]: https://imagej.net/update-sites/following
[maven]: https://imagej.net/develop/maven
