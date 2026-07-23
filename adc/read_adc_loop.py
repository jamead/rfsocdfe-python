import matplotlib.pyplot as plt
import scipy.signal as signal
import cothread
#from cothread.catools import caget
import epics
import numpy as np
import time

#datapts = 100000

Frf = 499.68e6
hIf = 1320
hADC = 310
#Fs = Frf/hIf*hADC
Fs = 117349090
adcFS = 32768 
numpts = 100000




def set_pv(bpms,pvname,val):

   bpms_pv = []
   for i in range(len(bpms)):
       bpms_pv.append(bpms[i]+"Tbt-sum")
   caput(bpms_pv,val)
 


def get_waveform(PVs,numpts):
  
  TBT_array = []
  for i in range(len(PVs)):
     TBT_array.append(PVs[i].get())

  waveform = np.asarray(TBT_array, dtype=np.float32)
  waveform = waveform[:,0:numpts] 
   
  return waveform 



def calc_psd(y):
   N = len(y)  
   print ("len(y)=%d" % N)
   #f = np.linspace(0,Fs/2,N/2+1)
   #print ("len(t)=%f" % len(adc_data))
   #print ("len(f)=%f" % len(f))
   #print ("Total Time=%f" % (Ts*N))
   #y = y / adcFS
   #y = y - np.mean(y)
   w = np.hanning(N)
   x = w * y
   xfft = np.abs(np.fft.rfft(x)) / (N/2.0)

   p = 20*np.log10(xfft)
   return p




def main():
  
  #plt.ion()

  import seaborn as sns
  sns.set_style("whitegrid")
  #plt.style.use('seaborn-whitegrid')
  plt.rc('font',size=8)

  adc_pv = []
  adc_pv.append(epics.PV('lab-BI{BPM:2}ADC:A:Buff-Wfm'))
  adc_pv.append(epics.PV('lab-BI{BPM:2}ADC:B:Buff-Wfm'))
  adc_pv.append(epics.PV('lab-BI{BPM:2}ADC:C:Buff-Wfm'))
  adc_pv.append(epics.PV('lab-BI{BPM:2}ADC:D:Buff-Wfm'))
  trig_pv = epics.PV('lab-BI{BPM:2}Trig:Strig-SP')

  Fs = 117349090
 
  adcA = np.zeros(numpts,dtype=np.int16)
  x = np.linspace(0,numpts-1,numpts)
  plt.ion()


  figure, axes = plt.subplots(nrows=2, ncols=1, figsize=(8,4))
  line1, = axes[0].plot(x,adcA) 
  line2, = axes[1].plot(x,adcA)
  axes[0].set_title('ADC Data')
  axes[0].set_xlabel('Sample #')
  axes[0].set_ylabel('adu')
  axes[0].set_ylim(-1,1) # 14-bit ADC range
  axes[0].grid(True)
  axes[1].set_xlabel('Freq')
  axes[1].set_ylabel('Power')
  axes[1].set_ylim(-160,10) # 14-bit ADC range
  axes[1].set_xlim(0,Fs/2/1e6)
  axes[1].grid(True)

  while True:

    trig_pv.put(1)
    time.sleep(2)   
    adc_data = get_waveform(adc_pv,numpts)
    print("Len adc_data = ",len(adc_data[0])) 
    adcA = adc_data[0] / 32768
    p = calc_psd(adcA)
    print(p)
    print("Plotting...")
    line1.set_xdata(x)
    line1.set_ydata(adcA)

    N = len(p)*2-1
    print("Fs = ",Fs)
    Fs=117349090
    f = np.linspace(0,Fs/2,N//2+1)
    f = f/1e6
        
    print("n = ",N)
    print("length f = ",len(f))
    print("length p = ",len(p))
    print("length adcA = ",len(adcA))

    line2.set_xdata(f)
    line2.set_ydata(p)
        
    figure.canvas.draw() 
    figure.canvas.flush_events()
    time.sleep(0.1) 






if __name__ == "__main__":
  main()

