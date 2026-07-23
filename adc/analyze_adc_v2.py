import matplotlib.pyplot as plt
import numpy as np
import sys


Frf = 499.68e6
hIf = 1320
hADC = 310
Fs = Frf / hIf * hADC


def read_adcdata(fname, maxpts=1000000):
    data = []

    with open(fname, "r") as fin:
        for linenum, line in enumerate(fin, start=1):
            if linenum > maxpts:
                break

            vals = line.strip().split()

            if len(vals) != 4:
                print("Error in line %d" % linenum)
                break

            data.append([float(vals[0]), float(vals[1]), float(vals[2]), float(vals[3])])

    adc_data = np.asarray(data, dtype=np.float32)

    print("Read %d ADC pts" % len(adc_data))
    print("ADC data shape:", adc_data.shape)

    return adc_data


def calc_snr_sfdr(y, ignore_bins=50):
    y = np.asarray(y, dtype=np.float64)
    y = y - np.mean(y)

    N = len(y)
    w = np.hanning(N)
    x = y * w

    xfft = np.abs(np.fft.rfft(x)) / (np.sum(w) / 2.0)
    power = xfft**2

    # Ignore DC
    power[0] = 0.0

    # Find fundamental
    fund_bin = np.argmax(power)
    fund_power = power[fund_bin]

    # Remove bins around fundamental from noise/spur search
    noise_power = power.copy()
    lo = max(0, fund_bin - ignore_bins)
    hi = min(len(power), fund_bin + ignore_bins + 1)
    noise_power[lo:hi] = 0.0

    total_noise_power = np.sum(noise_power)
    max_spur_power = np.max(noise_power)

    snr = 10.0 * np.log10(fund_power / total_noise_power)
    sfdr = 10.0 * np.log10(fund_power / max_spur_power)

    fund_freq = fund_bin * Fs / N
    spur_bin = np.argmax(noise_power)
    spur_freq = spur_bin * Fs / N

    return snr, sfdr, fund_freq, spur_freq






def calc_psd(y):
    y = np.asarray(y, dtype=np.float64)

    N = len(y)
    print("len(y)=%d" % N)

    # Remove DC
    y = y - np.mean(y)

    # Hann window
    w = np.hanning(N)
    x = y * w

    # FFT magnitude
    xfft = np.abs(np.fft.rfft(x))

    # Correct amplitude for Hann window coherent gain
    xfft = xfft / (np.sum(w) / 2.0)

    # Avoid log10(0)
    xfft = np.maximum(xfft, 1e-20)

    # Convert to dBFS
    p = 20.0 * np.log10(xfft)

    return p


def plot_psd(pa, pb, pc, pd):
    f = np.linspace(0, Fs / 2.0, len(pa)) / 1e6
    ylim = [-160, 0]

    fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(10, 6))
    ax1, ax2, ax3, ax4 = axes.flatten()

    ax1.plot(f, pa)
    ax1.set_ylabel("dBFS")
    ax1.set_title("PSD ChA")
    ax1.grid(True)

    ax2.plot(f, pb)
    ax2.set_title("PSD ChB")
    ax2.grid(True)

    ax3.plot(f, pc)
    ax3.set_xlabel("freq (MHz)")
    ax3.set_ylabel("dBFS")
    ax3.set_title("PSD ChC")
    ax3.grid(True)

    ax4.plot(f, pd)
    ax4.set_xlabel("freq (MHz)")
    ax4.set_title("PSD ChD")
    ax4.grid(True)

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_ylim(ylim)

    fig.tight_layout()
    plt.show(block=False)


def plot_adc(adc_data, max_plot_pts=2000):
    a = adc_data[:, 0]
    b = adc_data[:, 1]
    c = adc_data[:, 2]
    d = adc_data[:, 3]

    # Plot only first N points so it does not get too slow
    a = a[:max_plot_pts]
    b = b[:max_plot_pts]
    c = c[:max_plot_pts]
    d = d[:max_plot_pts]

    ymin = min(np.min(a), np.min(b), np.min(c), np.min(d))
    ymax = max(np.max(a), np.max(b), np.max(c), np.max(d))

    fig, axes = plt.subplots(2, 2, sharex=True, figsize=(8, 6))
    ax1, ax2, ax3, ax4 = axes.flatten()

    ax1.plot(a)
    ax1.set_ylabel("adu")
    ax1.set_title("ChA")
    ax1.set_ylim(ymin, ymax)
    ax1.grid(True)

    ax2.plot(b)
    ax2.set_ylabel("adu")
    ax2.set_title("ChB")
    ax2.set_ylim(ymin, ymax)
    ax2.grid(True)

    ax3.plot(c)
    ax3.set_ylabel("adu")
    ax3.set_xlabel("sample num")
    ax3.set_title("ChC")
    ax3.set_ylim(ymin, ymax)
    ax3.grid(True)

    ax4.plot(d)
    ax4.set_ylabel("adu")
    ax4.set_xlabel("sample num")
    ax4.set_title("ChD")
    ax4.set_ylim(ymin, ymax)
    ax4.grid(True)

    fig.tight_layout()
    plt.show(block=False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plot_adc.py input_file.txt")
        sys.exit(1)

    fname = sys.argv[1]

    print("Fs = %.6f MHz" % (Fs / 1e6))

    adc_data = read_adcdata(fname)

    if adc_data.shape[1] != 4:
        print("Error: expected 4 ADC columns")
        sys.exit(1)

    print("First sample:", adc_data[0])

    plot_adc(adc_data)

    # Convert ADC counts to full-scale units
    cha = adc_data[:, 0] / 32768.0
    chb = adc_data[:, 1] / 32768.0
    chc = adc_data[:, 2] / 32768.0
    chd = adc_data[:, 3] / 32768.0

    pa = calc_psd(cha)
    pb = calc_psd(chb)
    pc = calc_psd(chc)
    pd = calc_psd(chd)

    plot_psd(pa, pb, pc, pd)
    
    
    for name, ch in [("A", cha), ("B", chb), ("C", chc), ("D", chd)]:
        snr, sfdr, fund_freq, spur_freq = calc_snr_sfdr(ch)

    print(
        "Ch%s: SNR = %.2f dB, SFDR = %.2f dB, Fund = %.6f MHz, Spur = %.6f MHz"
        % (name, snr, sfdr, fund_freq / 1e6, spur_freq / 1e6)
    )

    plt.show()
    input("Press Enter to quit...")


if __name__ == "__main__":
    main()
