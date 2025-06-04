import logging
import os
import sys
import numpy as np


# Set up logging to help with Exceptions when parsing using Numpy
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


def convert_to_csv(path):
    """
    Reads a pear binary file and writes the decoded content to [path].csv.

    Args:
        path (str): The path to the binary file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError("You must specify a correct path to a pear file")

    # The data is a 2d array with 2 integer columns
    dtype = np.dtype([("Time (ms)", np.int32), ("Intensity", np.int32)])

    # The file has a fixed 480-byte footer. Calculate when to stop reading
    file_size = os.path.getsize(path)
    end_offset = file_size - 480  # stop reading data at the last 480-bytes

    # Data starts after a fixed header length of 320-bytes
    start_offset = 0x140
    data_section_size = end_offset - start_offset

    # Read the data section using numpy
    data = np.fromfile(path,
                       dtype=dtype,
                       count=data_section_size // np.dtype(dtype).itemsize,
                       offset=start_offset)
    logging.debug(f"start of data: {data[:6]}\nend of data: {data[-6:]}")

    # Save the data as a .csv file with column names
    # FYI Numpy adds a trailing newline at the end of the file, considering removing
    np.savetxt(fname=f"{path}.csv",
               X=data,
               delimiter=",",
               fmt="%d",
               header=",".join(dtype.names),
               comments="")


if __name__ == '__main__':
    convert_to_csv("pear/pear")
