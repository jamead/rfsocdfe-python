import sys

import matplotlib.pyplot as plt
import numpy as np


NUM_INPUT_SAMPLES = 13_200
SAMPLES_PER_SUM = 10
NUM_OUTPUT_POINTS = NUM_INPUT_SAMPLES // SAMPLES_PER_SUM

# Select which column to read:
# 0 = Channel A
# 1 = Channel B
# 2 = Channel C
# 3 = Channel D
ADC_CHANNEL = 0

Frf = 499.68e6
hIf = 1320
hADC = 310
Fs = Frf / hIf * hADC


def read_adcdata(fname, channel=ADC_CHANNEL):
    """
    Read one ADC channel from a four-column text file.

    Each line of the input file must contain:
        channel_A channel_B channel_C channel_D

    Only the first 13,200 valid samples are read.
    """
    adc_data = []

    if channel < 0 or channel > 3:
        raise ValueError("ADC channel must be between 0 and 3.")

    with open(fname, "r") as fin:
        for linenum, line in enumerate(fin, start=1):

            if len(adc_data) >= NUM_INPUT_SAMPLES:
                break

            values = line.split()

            if not values:
                continue

            if len(values) != 4:
                raise RuntimeError(
                    f"Line {linenum} contains {len(values)} values; "
                    "expected 4."
                )

            try:
                sample = float(values[channel])
            except ValueError as error:
                raise RuntimeError(
                    f"Invalid numeric data on line {linenum}."
                ) from error

            adc_data.append(sample)

    adc_data = np.asarray(adc_data, dtype=np.float32)

    if len(adc_data) < NUM_INPUT_SAMPLES:
        raise RuntimeError(
            f"Only {len(adc_data)} samples were read; "
            f"{NUM_INPUT_SAMPLES} samples are required."
        )

    print(f"Read {len(adc_data)} samples from ADC channel {channel}")
    print(f"ADC sample rate: {Fs / 1e6:.6f} MHz")

    return adc_data


def sum_absolute_samples(adc_data):
    """
    Take the absolute value of each sample, group the data into
    groups of 10 samples, and sum each group.

    This produces 1,320 output points from 13,200 input samples.
    """
    adc_data = adc_data[:NUM_INPUT_SAMPLES]

    absolute_data = np.abs(adc_data)

    grouped_data = absolute_data.reshape(
        NUM_OUTPUT_POINTS,
        SAMPLES_PER_SUM
    )

    summed_data = np.sum(grouped_data, axis=1)

    print(
        f"Created {len(summed_data)} points by summing "
        f"the absolute value of every {SAMPLES_PER_SUM} samples."
    )

    return summed_data


def plot_summed_data(summed_data):
    point_number = np.arange(len(summed_data))

    plt.figure(figsize=(11, 6))

    plt.plot(point_number, summed_data)

    plt.xlabel("Summed point number")
    plt.ylabel("Sum of absolute ADC samples")
    plt.title(
        "ADC Data: Sum of Absolute Value of Each 10 Samples"
    )

    plt.grid(True)
    plt.tight_layout()
    plt.show()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ADC data file>")
        sys.exit(1)

    fname = sys.argv[1]

    try:
        adc_data = read_adcdata(fname)
        summed_data = sum_absolute_samples(adc_data)

    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}")
        sys.exit(1)

    plot_summed_data(summed_data)


if __name__ == "__main__":
    main()

