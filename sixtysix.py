import logging
import os
import sys
import struct
from collections import OrderedDict
import numpy as np

# Set up logging to help with Exceptions when parsing using Numpy
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


def convert_to_csv(output_filename, a_path, b_path):
    """
    Reads a sixtysix binary file and writes the decoded content to [path].csv.

    Args:
        path (str): The path to the binary file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(a_path) or not os.path.exists(b_path):
        raise FileNotFoundError("You must specify a correct path to a sixtysix file")

    # Read time values from .A file
    raw_time_values = []
    num_intensities = []
    max_value = 0
    f = open(a_path, "rb")
    while True:
        val = f.read(10)
        if val is None or len(val) < 10:
            break

        # process 10 bytes at a time which represent each row
        time_encoded = struct.unpack('>H', val[6:8])[0]
        raw_time_values.append(time_encoded)
        max_value = time_encoded if time_encoded > max_value else max_value

        # each time (row) has a number representing number of values seen (rest of values are 0)
        num_intensities_in_row = struct.unpack('>h', val[8:10])[0]
        num_intensities.append(num_intensities_in_row)

    f.close()
    # decode time values
    time_values = np.array(raw_time_values)
    time_values = np.round(time_values / 60000, 4)
    formatted_time_values = np.array([f"{time:.4f}" for time in time_values])

    # Read mass & intensity values from .B file
    mass_values = set()
    mass_intensity_pairs = []
    f = open(b_path, "rb")
    while True:
        val = f.read(6)
        if val is None or len(val) < 6:
            break
        mass = struct.unpack('<h', val[:2])[0]
        intensity = struct.unpack('<i', val[2:6])[0]
        mass_intensity_pairs.append((mass, intensity))
        mass_values.add(mass)

    f.close()
    mass_values_sorted = sorted(mass_values)
    print(mass_values_sorted)

    # Combine mass, intensity, time data from top to bottom
    data_lines = []
    row_default = dict.fromkeys(mass_values_sorted, 0)  # Python 3.6+ maintains order of insertion
    for time in formatted_time_values:
        print(time)
        row = row_default.copy()
        num_intensities_in_row = num_intensities.pop(0)
        for _ in range(num_intensities_in_row):
            mass_intensity_pair = mass_intensity_pairs.pop(0)
            mass = mass_intensity_pair[0]
            intensity = mass_intensity_pair[1]
            row[mass] = intensity
        data_lines.append(list(row.values()))

    # Write file
    header = "Time (min)"
    for mass in mass_values_sorted:
        header += f",{mass}"

    with open(output_filename, "w") as file:
        file.write(header)
        for time in formatted_time_values:
            line = data_lines.pop(0)
            line_printed = ",".join(map(str, line))
            row = f"{time},{line_printed}"
            file.write("\n")
            file.write(row)

    logging.info(f"{output_filename} written successfully")


if __name__ == '__main__':
    convert_to_csv(output_filename="sixtysix/sixtysix.csv",
                   a_path="sixtysix/sixtysix.A",
                   b_path="sixtysix/sixtysix.B")
