import logging
import os
import sys
import struct
import numpy as np


# Set up logging to help with Exceptions when parsing using Numpy
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


def convert_to_csv(path):
    """
    Reads a scale binary file and writes the decoded content to [path].csv.

    Args:
        path (str): The path to the binary file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError("You must specify a correct path to a scale file")

    # File offsets to begin reading absorbance factor and then main data
    factor_offset = 0x81
    data_offset = 0x200

    f = open(path, "rb")

    # Read factor used as a divisor for the absorbance values
    f.seek(factor_offset)
    absorbance_factor = struct.unpack("<i", f.read(4))[0]

    # Data starts at a fixed offset
    f.seek(data_offset)

    # Read 1 section (row) of data at a time and append to a table list
    table = []
    while True:
        # Each row starts with "HH" - you can see the pattern in hexdump
        row_header = f.read(2)
        if not row_header:
            logging.info("End of file reached")
            break
        if row_header != b'HH':
            raise IOError(f"Found invalid row header while parsing {path}")

        data_row = []

        # Read 1st of 23 total columns since it is a float
        b = f.read(4)
        data = struct.unpack("<f", b)[0]
        data_row.append(data)

        # Read remaining 22 values (columns) as signed integers
        for i in range(22):
            val = f.read(4)
            val = struct.unpack(">i", val)[0]
            val = int(val / absorbance_factor)
            data_row.append(val)

        # Store row of data
        table.append(data_row)

    logging.debug(f"Last row of data: {table[-1:]}")

    # Save the data as a .csv file with column names
    header = "Time (min),190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400\n"
    file_csv = f"{path}.csv"
    with open(file_csv, "w") as file:
        file.write(header)
        rows = []
        for row in table:
            rows.append(",".join(f"{r:.4f}" if i == 0 else str(r) for i, r in enumerate(row)))
        file.write("\n".join(rows))
    logging.info(f"{file_csv} written successfully")


if __name__ == '__main__':
    convert_to_csv("scale/scale")
