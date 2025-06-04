## Merck Coding Challenge by Jonathan Olson
My resume is included in this repo, see: Resume_Jonathan_Olson.pdf

Contact: jonnycoder@gmail.com

This was a fun and challenging coding assignment. I just noticed that the 
coding challenge instructions have been updated with an email for reaching 
out about questions. I wish about that before completing the 
majority of the assignment, as I have many questions!



## Code Dependencies

- Run the following in the terminal to create a virtual environment and install dependencies:
```
python -m venv venv
source venv/bin/activate
pip install pyplate-hte
pip install rainbow-api
pip install numpy
```

## Part 1: PyPlate Feature

The file, PyPlate_Recipe.ipynb, is in this repo and was created and tested 
in Google Colab. 

The route I chose was to split the 200 uL reaction volume into 4 equal parts: 50 uL each 
for Ai, Bi, ligand and catalyst. I created solutions using each of the four 
solvents, but used different concentrations based on the requirements.

As an experienced software engineer, I do not have a background in chromatography or chemistry, 
therefore I made a few assumptions which are documented as comments in the notebook.

After spending many hours implementing part (a), one aspect I overlooked was the ability 
of the Container object to hold substances without the need for a liquid solvent. I 
discovered this near the end. I am now confident there is a simpler implementation for part (a).


### Part B: Tagging Feature

Adding tags and relative quantities would be straightforward change to the Substance and 
Container classes. Additional checks, such as using a Set to track all tags, would be 
needed to ensure a tag is unique and not used by any other substance.

The **Substance** class would take an optional tags array:
```
"""
An abstract chemical or biological entity (e.g., reagent, enzyme, solvent, etc.). Immutable.
Enzymes are assumed to require zero volume.

Attributes:
    name: Name of substance.
    tags (list): (Optional) List of tag names.
    mol_weight: Molecular weight (g/mol).
    density: Density if `Substance` is a liquid (g/mL).
    concentration: Calculated concentration if `Substance` is a liquid (mol/mL).
    molecule: `cctk.Molecule` if provided.
"""
```

The **Container** class method **transfer** would be modified such that the quantity 
parameter could accept a relative quantity of a tagged substance if an only if the substance 
belongs in the source container. 

When using relative quantity, extra checks would be needed to ensure the tag is found in 
the source container and the source container contains enough source quantity needed in 
the transfer. The container has a max_volume which to not be exceeded. The most complicated 
quality assurance check would involve checking the concentration consistency if the container 
is liquid.
```
"""
Move quantity ('10 mL', '5 mg', '1.1 * A') from source to destination container,
returning copies of the objects with amounts adjusted accordingly.

Arguments:
    source: Container, plate, or slice to transfer from.
    destination: Container to transfer to:
    quantity: How much to transfer. Volume, mass or relative source substance.

Returns:
    A tuple of (T, Container) where T is the type of the source.
"""
```



## Usage
Ensure the pear directory exists with the pear binary file and run: 
```
python pear.py
```
If you want to use it as a module, you can use the following code:
```
import pear
pear.convert_to_csv("pear/pear")
```


## Part 2: Decoding Binary Data

### Decoding "pear" Data Structure

#### Header Section
The pear binary file has a fixed header section, of 320 bytes, with repeating
`H...H...H...H...` (ASCII or UTF-8 character set) up until offset `0x140`. 

#### Footer Section
A fixed footer section exists with repeating `F...F...F...F...` (ASCII or UTF-8 character set) 
occupying the last 480 bytes.

#### Data Section
The data section contains continuous 4-byte integers in little endian format, which are 
read using Numpy. We read the data section up until end-of-file minus 480 bytes. Each row 
in the csv file is a pair of integers, therefore 0x140 through 0x148 represent the first row.

Numpy and its fromfile method are used to read the binary file due to the simple nature of the format, 
as well as the potential benefit of using this method in the future.


### Decoding "scale" Data Structure

#### Header Section
The scale binary file appears to have a fixed header section of 512 bytes.

| File Offset | Data Type       | Endianness | Decoded Value | Purpose                                                   |
|-------------|-----------------|------------|---------------|-----------------------------------------------------------|
| 0x80        | Short (4-bytes) | Big        | 20            | Absorbance factor acting as divisor to absorbance values  |
| 0x100       | Short (4-bytes) | Big        | 190           | Wavelength start value                                    |
| 0x102       | Short (4-bytes) | Big        | 400           | Wavelength end value                                      |
| 0x104       | Short (4-bytes) | Big        | 10            | Wavelength interval/step value                            |
| 0x180       | Short (4-bytes) | Big        | 12345         | Number of rows of data                                    |



#### Data Section
The data section begins at offset `0x200`, which is indicated by the first instance of `HH`. 
There are 94-bytes for each row of data, and each row is repeated until the end of the file.

The first 2-bytes represent the data row header with the value of 'HH' (ASCII or UTF-8 character set).

The Next 92-bytes consists of the data row values.
The first 4 bytes is a little-endian float representing time value, to 4 decimal places (scale of 4).
Each additional 4-bytes is a big-endian signed integer as the 22 absorbance values for wavelengths 190 to 400.


### Decoding "sixtysix" Data Structure

#### sixtysix.A
This file does not appear to contain any header or footer information.
There are 5432 rows of data in the target sixtysix_original.csv, and sixtysix.A has a file size of 54320 bytes.
Therefore, each 10 byte of data has some information useful for each row in the csv file.

The data begins at the start of the binary file.

For each 10 byte data segment:

* The first 6 bytes may represent additional information but that is undetermined at this time.

* Bytes 7 and 8 is a big endian unsigned short to represent encoded time values.

* The last 2 bytes is a big endian short representing the number of mass/intensity values during each segment (time value).
This is used to reconstruct the csv file line by line.

To decode each time value, we divide each encoded time value by the maximum time value found, 
or 60000 in sixtysix.A, and round to 4 decimal places. 



#### sixtysix.B
This file does not appear to contain any header or footer information.
The data is read 6 bytes at a time starting at the beginning of the file, and each 6 bytes is 
a key-value pair of mass and intensity values in the same order as the time values from sixtysix.A file.

For each 6 byte section, the first 2 bytes is a little endian short representing mass.
The remaining 4 bytes is a little endian signed integer representing the intensity value for the previous mass value.

The data section is read until the end of the file.

The csv file is reconstructed line by line, where each value in num_intensities_in_row array 
tells us the number of mass/intensity pairs to pop off the head of the list and add to each time period (row).


#### sixtysix.C
sixtysix.C is a compressed binary file:
```
file sixtysix.C   
sixtysix.C: gzip compressed data, last modified: Fri Aug  5 18:55:13 2022, max compression, original size modulo 2^32 3800000
```

To extract the file, run: `gunzip -S .C sixtysix.C`

The contents of the extracted file has the repeating text: `There Is Nothing Useful In This File.`


