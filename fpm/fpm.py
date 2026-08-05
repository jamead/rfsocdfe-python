import matplotlib.pyplot as plt
import numpy as np
import cothread
import epics
import time
import argparse

NUM_INPUT_SAMPLES = 13_200
SAMPLES_PER_SUM = 10
NUM_OUTPUT_POINTS = NUM_INPUT_SAMPLES // SAMPLES_PER_SUM

Frf = 499.68e6
hIf = 1320
hADC = 310
Fs = Frf / hIf * hADC


def get_waveform(PV, start_sample, numpts):
    """
    Read a waveform from an EPICS PV and return the requested
    window of samples.
    """
    waveform = np.asarray(PV.get(), dtype=np.float32)

    if start_sample + numpts > len(waveform):
        raise ValueError(
            f"Requested samples {start_sample} to "
            f"{start_sample + numpts - 1}, but waveform "
            f"contains only {len(waveform)} samples."
        )

    return waveform[start_sample:start_sample + numpts]


def sum_absolute_samples(adc_data):
    """
    Take the absolute value of each sample, group the data into
    groups of 10 samples, and sum each group.
    """
    absolute_data = np.abs(adc_data)

    grouped_data = absolute_data.reshape(
        NUM_OUTPUT_POINTS,
        SAMPLES_PER_SUM
    )

    return np.sum(grouped_data, axis=1)


def normalize_summed_data(summed_data,dcct):
    """
    Normalize each individual sum by the total sum.

    The returned normalized points will add up to 1.0.
    """
    total_sum = np.sum(summed_data)

    if total_sum == 0:
        normalized_data = np.zeros_like(
            summed_data,
            dtype=np.float64
        )
    else:
        normalized_data = summed_data / total_sum * dcct

    return normalized_data, total_sum


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Display raw ADC waveform and normalized "
            "10-sample absolute-value sums."
        )
    )

    parser.add_argument(
        "bpm_prefix",
        type=str,
        help="BPM prefix (e.g. lab-BI{BPM:2})"
    )

    parser.add_argument(
        "-s",
        "--start-sample",
        type=int,
        default=0,
        help="Starting ADC sample. Default = 0"
    )

    args = parser.parse_args()

    if args.start_sample < 0:
        parser.error("--start-sample must be zero or greater")

    bpm_prefix = args.bpm_prefix
    start_sample = args.start_sample

    adc_pv = epics.PV(bpm_prefix + "ADC:A:Buff-Wfm")
    trig_pv = epics.PV(bpm_prefix + "Trig:Soft-SP")
    dcct_pv = epics.PV("SR:C03-BI{DCCT:1}I:Real-I")
    

    plt.ion()

    #
    # Raw ADC waveform
    #
    fig_adc, ax_adc = plt.subplots(
        figsize=(11, 4)
    )

    line_adc, = ax_adc.plot(
        [],
        [],
        lw=1
    )

    ax_adc.set_title(
        f"Raw ADC Waveform "
        f"(Start Sample = {start_sample})"
    )

    ax_adc.set_xlabel("ADC Sample")
    ax_adc.set_ylabel("ADC Counts")
    ax_adc.set_xlim(0,NUM_INPUT_SAMPLES - 1)
    ax_adc.set_ylim(-5000,5000)
    ax_adc.grid(True)

    #
    # Normalized summed waveform
    #
    fig_sum, ax_sum = plt.subplots(
        figsize=(11, 4)
    )

    line_sum, = ax_sum.plot(
        [],
        [],
        lw=1.5
    )

    ax_sum.set_title(
        "Normalized Sum of |ADC| Every 10 Samples"
    )

    ax_sum.set_xlabel("Summed Point")

    ax_sum.set_ylabel(
        "Individual Sum / Total Sum"
    )

    ax_sum.set_xlim(
        0,
        NUM_OUTPUT_POINTS - 1
    )

    # A typical value is approximately 1 / 1320
    # or about 0.000758.
    ax_sum.set_ylim(
        0,
        1
    )

    ax_sum.grid(True)

    try:
        while True:

            # Uncomment if a software trigger is required.
            # trig_pv.put(1)

            #dcct = dcct_pv.get();
            dcct = 500.0
            print(f"DCCT = {dcct:,.2f}")
            
            adc_data = get_waveform(
                adc_pv,
                start_sample,
                NUM_INPUT_SAMPLES
            )

            summed_data = sum_absolute_samples(
                adc_data
            )

            normalized_data, total_sum = (
                normalize_summed_data(summed_data,dcct)
            )

            print(
                f"Total |ADC| Sum = {total_sum:,.0f}, "
                f"Normalized Sum = "
                f"{np.sum(normalized_data):.6f}"
            )

            #
            # Update raw ADC plot
            #
            x_adc = np.arange(
                NUM_INPUT_SAMPLES
            )

            line_adc.set_data(
                x_adc,
                adc_data
            )

            #
            # Update normalized summed waveform
            #
            x_sum = np.arange(
                NUM_OUTPUT_POINTS
            )

            line_sum.set_data(
                x_sum,
                normalized_data
            )

            #
            # Refresh figures
            #
            fig_adc.canvas.draw()
            fig_adc.canvas.flush_events()

            fig_sum.canvas.draw()
            fig_sum.canvas.flush_events()

            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopped.")

    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
