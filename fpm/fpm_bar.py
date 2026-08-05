import argparse
import time

import cothread
import epics
import matplotlib.pyplot as plt
import numpy as np


NUM_INPUT_SAMPLES = 13_200
SAMPLES_PER_SUM = 10
NUM_OUTPUT_POINTS = NUM_INPUT_SAMPLES // SAMPLES_PER_SUM

Frf = 499.68e6
hIf = 1320
hADC = 310
Fs = Frf / hIf * hADC


def get_waveform(pv, start_sample, numpts):
    """
    Read an EPICS waveform PV and return the requested
    range of samples.
    """
    waveform = pv.get(timeout=2.0)

    if waveform is None:
        raise RuntimeError(
            f"Unable to read waveform PV: {pv.pvname}"
        )

    waveform = np.asarray(
        waveform,
        dtype=np.float64
    )

    end_sample = start_sample + numpts

    if end_sample > len(waveform):
        raise ValueError(
            f"Requested samples {start_sample} through "
            f"{end_sample - 1}, but PV {pv.pvname} contains "
            f"only {len(waveform)} samples."
        )

    return waveform[start_sample:end_sample]


def sum_absolute_samples(adc_data):
    """
    Take the absolute value of every ADC sample, divide the
    waveform into groups of 10 samples, and sum each group.
    """
    absolute_data = np.abs(adc_data)

    grouped_data = absolute_data.reshape(
        NUM_OUTPUT_POINTS,
        SAMPLES_PER_SUM
    )

    summed_data = np.sum(
        grouped_data,
        axis=1
    )

    return summed_data


def normalize_summed_data(summed_data,dcct):
    """
    Divide each individual 10-sample sum by the overall sum.

    The returned normalized values add up to 1.0.
    """
    total_sum = np.sum(summed_data)

    if total_sum <= 0:
        normalized_data = np.zeros(
            len(summed_data),
            dtype=np.float64
        )
    else:
        normalized_data = summed_data / total_sum * dcct

    return normalized_data, total_sum


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Display the raw ADC waveform and a bar plot "
            "of normalized 10-sample absolute-value sums."
        )
    )

    parser.add_argument(
        "bpm_prefix",
        type=str,
        help="BPM prefix, for example: lab-BI{BPM:2}"
    )

    parser.add_argument(
        "-s",
        "--start-sample",
        type=int,
        default=0,
        help="Starting ADC sample. Default: 0"
    )

    args = parser.parse_args()

    if args.start_sample < 0:
        parser.error(
            "--start-sample must be zero or greater"
        )

    bpm_prefix = args.bpm_prefix
    start_sample = args.start_sample

    adc_pv = epics.PV(
        bpm_prefix + "ADC:A:Buff-Wfm"
    )

    trig_pv = epics.PV(
        bpm_prefix + "Trig:Soft-SP"
    )
    
    dcct_pv = epics.PV("SR:C03-BI{DCCT:1}I:Real-I")

    print(f"Connecting to {adc_pv.pvname}")

    if not adc_pv.wait_for_connection(timeout=5.0):
        raise RuntimeError(
            f"Unable to connect to ADC PV: {adc_pv.pvname}"
        )

    plt.ion()

    #
    # Raw ADC waveform plot
    #
    fig_adc, ax_adc = plt.subplots(
        figsize=(11, 4)
    )

    x_adc = np.arange(NUM_INPUT_SAMPLES)

    line_adc, = ax_adc.plot(
        x_adc,
        np.zeros(NUM_INPUT_SAMPLES),
        linewidth=1
    )

    ax_adc.set_title(
        f"Raw ADC Waveform "
        f"(Start Sample = {start_sample})"
    )

    ax_adc.set_xlabel("ADC Sample")
    ax_adc.set_ylabel("ADC Counts")

    ax_adc.set_xlim(
        0,
        NUM_INPUT_SAMPLES - 1
    )

    ax_adc.set_ylim(
        -5000,
        5000
    )

    ax_adc.grid(True)

    fig_adc.tight_layout()

    #
    # Normalized summed-data bar plot
    #
    fig_sum, ax_sum = plt.subplots(
        figsize=(11, 4)
    )

    x_sum = np.arange(NUM_OUTPUT_POINTS)

    bars_sum = ax_sum.bar(
        x_sum,
        np.zeros(NUM_OUTPUT_POINTS),
        width=1.0
    )

    ax_sum.set_title(
        "Fill Pattern"
    )

    ax_sum.set_xlabel("Bucket Number")
    ax_sum.set_ylabel("Bunch (mA)")

    ax_sum.set_xlim(
        -0.5,
        NUM_OUTPUT_POINTS - 0.5
    )

    # The average normalized value is 1 / 1320,
    # which is approximately 0.000758.
    ax_sum.set_ylim(
        0,
        1
    )

    ax_sum.grid(
        True,
        axis="y"
    )

    fig_sum.tight_layout()

    try:
        while True:

            # Uncomment this line if a software trigger
            # is required before reading the waveform.
            #
            # trig_pv.put(1)
            # time.sleep(0.1)
            
            #dcct = dcct_pv.get();
            dcct = 500.0
            print(f"DCCT = {dcct:,.2f}")

            try:
                adc_data = get_waveform(
                    adc_pv,
                    start_sample,
                    NUM_INPUT_SAMPLES
                )

            except (RuntimeError, ValueError) as error:
                print(error)
                time.sleep(1)
                continue

            summed_data = sum_absolute_samples(
                adc_data
            )

            normalized_data, total_sum = (
                normalize_summed_data(summed_data, dcct)
            )

            print(
                f"Total |ADC| Sum = {total_sum:,.0f}, "
                f"Normalized Sum = "
                f"{np.sum(normalized_data):.6f}"
            )

            #
            # Update raw ADC waveform
            #
            line_adc.set_ydata(adc_data)

            #
            # Update normalized bar heights
            #
            for bar, value in zip(
                bars_sum,
                normalized_data
            ):
                bar.set_height(value)

            #
            # Increase the vertical range if a bar
            # exceeds the current fixed range.
            #
            maximum_value = np.max(normalized_data)

            if maximum_value > 0:
                current_top = ax_sum.get_ylim()[1]
                required_top = maximum_value * 1.10

                if required_top > current_top:
                    ax_sum.set_ylim(
                        0,
                        required_top
                    )

            #
            # Refresh plots
            #
            fig_adc.canvas.draw_idle()
            fig_adc.canvas.flush_events()

            fig_sum.canvas.draw_idle()
            fig_sum.canvas.flush_events()

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped.")

    finally:
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()
