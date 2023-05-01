import numpy as np
import matplotlib.pyplot as plt

from adbs_decode_symbols import adbs_decode_symbols


#############################################
# Load data
#############################################

filename = 'recordings/896478_live.complex16u'
#filename = 'recordings/message.complex16u'

Fs = 2000000

iq_data = np.fromfile(filename, dtype=np.uint8)
iq_data = iq_data.view(np.int8)
iq_data -= 128

signal_i = iq_data[::2]
signal_q = iq_data[1::2]

signal = signal_i + 1j*signal_q


print(f"Signal lenght: {signal.shape[0]}")
t = 1/Fs * np.arange(signal.shape[0])

#############################################
plt.figure("Signal view", figsize=(7,5.5))

plt.subplot(311)
plt.title("I")
plt.plot(t, np.real(signal))
plt.grid(True)

plt.subplot(312)
plt.title("Q")
plt.plot(t, np.imag(signal))
plt.grid(True)

plt.subplot(313)
plt.title("analog")
plt.plot(t, np.absolute(signal))
plt.grid(True)

#############################################
# Extract symbols
#############################################

demod_signal = np.absolute(signal)
noise = np.mean(demod_signal)
print(f"Noise: {noise}")

demod_noise_free = demod_signal-noise
demod_noise_free = np.where(demod_noise_free > 0.0, demod_noise_free, 0)

majority_upper_thr = np.median(demod_noise_free[demod_noise_free>0])
thr = majority_upper_thr*0.25
print(f"Thr: {thr}")

symbols = np.where(demod_noise_free > thr, 1, 0)
print(f"Symbols:\n{repr(symbols)}")

#############################################
plt.figure("Demod", figsize=(7,5.5))

plt.subplot(311)
plt.title("demod amplitude")
plt.plot(t, demod_signal)
plt.axhline(y=noise, color='r', linestyle=':')
plt.yticks([noise],['Noise level'], rotation=45)
plt.grid(True)

plt.subplot(312)
plt.title("Noise Free")
plt.plot(t, demod_noise_free)
plt.axhline(y=thr, color='r', linestyle=':')
plt.yticks([thr],['0 - 1 threshold'], rotation=45)
plt.grid(True)

plt.subplot(313)
plt.title("Symbols")
plt.plot(t, symbols)
plt.grid(True)

#############################################
# Find messages
#############################################

preamble = np.array([1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0])
msg_end = np.array([0,0,0])  # imposible in manchester encoding. Edge cases with 1 message after other but okaish

preamble_detected = False
start_index = None
for i in range(len(symbols)-len(preamble)):
    if not preamble_detected and np.array_equal(symbols[i:i+len(preamble)], preamble):
        print(f"Found start at {i}")
        start_index = i
        preamble_detected = True
    elif preamble_detected and np.array_equal(symbols[i+len(preamble):i+len(preamble)+len(msg_end)], msg_end):
        print(f"Found ending at {i+len(preamble)-1}")
        preamble_detected = False
        full_message = symbols[start_index:i+len(preamble)]
        print(full_message)
        print()
        adbs_decode_symbols(''.join(str(i) for i in full_message))
        


plt.show()


