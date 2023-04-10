import numpy as np
import cProfile as profile
import pstats
import matplotlib.pyplot as plt

from rtlsdr import RtlSdr

from adbs_decode_bits import adbs_decode_bits

#filename = '896478_live.complex16u'  # 8d8964789909de8f30049352c619
#filename = 'message.complex16u'  # 8f4d2023587790bba5998227c948
filename = 'usefull_to_compare.bin'

BUFFER_SIZE = 256 * 1024 # 256K IQ samples
#BUFFER_SIZE = 1000

ADBS_PREAMBLE_SYM = 16
ADBS_MSG_LEN_BITS = 112
ADBS_MSG_LEN_SYM = ADBS_MSG_LEN_BITS*2
ADBS_PACKET_LEN_SYM = ADBS_PREAMBLE_SYM + ADBS_MSG_LEN_SYM

# Convert from I and Q uint8 samples to amplitude
def demodulate_iq(iq_data: np.ndarray) -> np.ndarray:
    iq_data = iq_data.astype(np.int16)
    iq_data -= 128

    signal_i = iq_data[::2]
    signal_q = iq_data[1::2]

    demod_signal = np.array(signal_i**2 + signal_q**2)

    return demod_signal


def decode_symbols(demod_signal: np.ndarray):

    stats = 0
    adbs_message_b = np.zeros(ADBS_MSG_LEN_BITS , np.uint8)
    for i in range(demod_signal.size - ADBS_PACKET_LEN_SYM):

        ##### PREAMLE #####
        if not (demod_signal[i+0] > demod_signal[i+1] and \
                demod_signal[i+2] > demod_signal[i+3] and \
                demod_signal[i+4] < demod_signal[i+0] and \
                demod_signal[i+5] < demod_signal[i+0] and \
                demod_signal[i+6] < demod_signal[i+7] and \
                demod_signal[i+8] < demod_signal[i+9]):
            continue
        
        high = (demod_signal[i+0]+demod_signal[i+2]+demod_signal[i+7]+demod_signal[i+9]) / 8

        if not (high > demod_signal[i+11] and \
                high > demod_signal[i+12] and \
                high > demod_signal[i+13] and \
                high > demod_signal[i+14]):
            continue
        #print(f"Preamble OK: {np.array2string(demod_signal[i:i+16], max_line_width=100, precision=2)}")

        ##### DECODE SYMBOLS #####
        adbs_message_s = demod_signal[i+ADBS_PREAMBLE_SYM:i+ADBS_PACKET_LEN_SYM]

        error = False
        for (i, (first, second)) in enumerate(adbs_message_s.reshape(ADBS_MSG_LEN_BITS, 2)):
            if first > second:
                adbs_message_b[i] = 1
            elif first < second:
                adbs_message_b[i] = 0
            else:
                error = True
                break
        
        if error:
            #print("ERROR: 2 symbols with the same value")
            continue

        ##### DECODE BITS #####
        stats += adbs_decode_bits(''.join(str(i) for i in adbs_message_b), filter_df=17)

    return stats

def read_from_file(offset):
    
    iq_data = np.fromfile(filename, dtype=np.uint8, count=BUFFER_SIZE, offset=offset)
    offset += BUFFER_SIZE

    return iq_data, iq_data.size, offset
    


if __name__ == '__main__':

    rff = False

    prof = profile.Profile()
    prof.enable()

    demod_signal = np.zeros(BUFFER_SIZE//2 + ADBS_PACKET_LEN_SYM)
    offset = 0
    stats = 0

    if not rff:
        print("Using rtlsdr")
        sdr = RtlSdr()
        sdr.sample_rate = 2e6
        sdr.center_freq = 1090e6
        sdr.gain = 'auto'

    while True:

        if rff:
            iq_data, read_size, offset = read_from_file(offset)
            if read_size == 0:
                break
        else:
            # TODO: Do it async
            iq_data = np.ctypeslib.as_array(sdr.read_bytes(BUFFER_SIZE))
            read_size = BUFFER_SIZE

        # Save last bits for messages between 2 buffers
        demod_signal[ADBS_PACKET_LEN_SYM:ADBS_PACKET_LEN_SYM + read_size//2] = demodulate_iq(iq_data)

        stats += decode_symbols(demod_signal)

        # Save last un-iterated symbols for next iteration
        demod_signal[:ADBS_PACKET_LEN_SYM] = demod_signal[-ADBS_PACKET_LEN_SYM:]

    print(stats)

    prof.disable()
    stats = pstats.Stats(prof).strip_dirs().sort_stats("tottime")
    stats.print_stats(10) # top 10 rows