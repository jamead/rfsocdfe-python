import matplotlib.pyplot as plt
import scipy.signal as signal
import cothread

import epics
import numpy as np
import time
import sys

datapts = 100000

Frf = 499.68e6
hIf = 1320
hADC = 310
Fs = Frf/hIf*hADC*40

def read_adcdata(fname):
   a = []
   b = []
   c = []
   d = []

   linenum = 0
   maxpts = 1000000

   with open(fname, 'r') as fin:
      for line in fin:
         linenum += 1
         data = line.strip('\n').split()

         if len(data) != 4:
            print("Error in line %d" % linenum)
            break
         elif linenum > maxpts:
            break
         else:
            a.append(float(data[0]))
            b.append(float(data[1]))
            c.append(float(data[2]))
            d.append(float(data[3]))

   a = np.array(a, dtype=np.float32)
   b = np.array(b, dtype=np.float32)
   c = np.array(c, dtype=np.float32)
   d = np.array(d, dtype=np.float32)

   # Remove DC offset (subtract mean)
   a = a - np.mean(a)
   b = b - np.mean(b)
   c = c - np.mean(c)
   d = d - np.mean(d)

   print("Read %d ADC pts" % linenum)
   print("Means removed:")
   print("A = %.3f" % np.mean(a))
   print("B = %.3f" % np.mean(b))
   print("C = %.3f" % np.mean(c))
   print("D = %.3f" % np.mean(d))

   n = len(a)
   adc_data = np.zeros((n, 4), dtype=np.float32)

   print("Length = %d" % n)

   adc_data[:,0] = a
   adc_data[:,1] = b
   adc_data[:,2] = c
   adc_data[:,3] = d

   return adc_data



def calc_stats(bpms,tbtsum):

  #calc stats
  tbts_std = []
  tbts_mean = []
  
  for i in range(len(bpms)):
     tbts_std.append(np.std(tbtsum[i])) 
     tbts_mean.append(np.mean(tbtsum[i])) 

  #print results 
  for i in range(len(bpms)):
     print('%d:  %s  mean:%f  std:%f'  % (i, bpms[i], tbts_mean[i], tbts_std[i]))

  return tbts_std, tbts_mean


def calc_psd(y):
   N = len(y)  
   print ("len(y)=%d" % N)

   w = np.hanning(N)
   x = w * y
   xfft = np.abs(np.fft.rfft(x)) / (N/2.0)

   p = 20*np.log10(xfft)
   return p



def plot_psd(a, b, c, d):

    N = len(a) * 2 - 1
    f = np.linspace(0, Fs/2, N//2 + 1) / 1e6  # freq in MHz
    ylim = [-160, 0]

    fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(10, 6))
    ax1, ax2, ax3, ax4 = axes.flatten()

    # Channel A
    ax1.plot(f, a, 'b')
    ax1.set_ylabel('dBFS')
    ax1.set_title('PSD ChA')
    ax1.grid(True)

    # Channel B
    ax2.plot(f, b, 'b')
    ax2.set_title('PSD ChB')
    ax2.grid(True)

    # Channel C
    ax3.plot(f, c, 'b')
    ax3.set_xlabel('freq (MHz)')
    ax3.set_ylabel('dBFS')
    ax3.set_title('PSD ChC')
    ax3.grid(True)

    # Channel D
    ax4.plot(f, d, 'b')
    ax4.set_xlabel('freq (MHz)')
    ax4.set_title('PSD ChD')
    ax4.grid(True)

    # Apply same y limits to all
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_ylim(ylim)

    fig.tight_layout()
    plt.show(block=False)





def plot_adc(adc_data):
    a = adc_data[:,0]
    b = adc_data[:,1]
    c = adc_data[:,2]
    d = adc_data[:,3]


    # Compute global y-limits
    ymin = min(map(min, [a, b, c, d]))
    ymax = max(map(max, [a, b, c, d]))

    fig, axes = plt.subplots(2, 2, sharex=True, figsize=(8, 6))
    ax1, ax2, ax3, ax4 = axes.flatten()

    ax1.plot(a, 'b-o')
    ax1.set_ylabel('adu')
    ax1.set_title('ChA')
    ax1.set_ylim(ymin, ymax)
    ax1.grid(True)

    ax2.plot(b, 'b-o')
    ax2.set_ylabel('adu')
    ax2.set_title('ChB')
    ax2.set_ylim(ymin, ymax)
    ax2.grid(True)

    ax3.plot(c, 'b-o')
    ax3.set_ylabel('adu')
    ax3.set_xlabel('sample num')
    ax3.set_title('ChC')
    ax3.set_ylim(ymin, ymax)
    ax3.grid(True)

    ax4.plot(d, 'b-o')
    ax4.set_ylabel('adu')
    ax4.set_xlabel('sample num')
    ax4.set_title('ChD')
    ax4.set_ylim(ymin, ymax)
    ax4.grid(True)

    fig.tight_layout()
    plt.show(block=False)



def main():
  

   if len(sys.argv) != 2:
       print ("Missing input file...")
       sys.exit() 
   else:
       fname = sys.argv[1]


   adc_data=read_adcdata(fname)
   print(adc_data[0])     
   print(adc_data.shape) 
   plot_adc(adc_data)


   pa = calc_psd(adc_data[:,0]/32768)
   pb = calc_psd(adc_data[:,1]/32768)
   pc = calc_psd(adc_data[:,2]/32768)
   pd = calc_psd(adc_data[:,3]/32768)

   plot_psd(pa,pb,pc,pd) 
 
   
   #plot_psd(fa_data,Ffa)
   

   
   plt.show()
   plt.draw()
   input('Press any key to quit...')




if __name__ == "__main__":
  main()

