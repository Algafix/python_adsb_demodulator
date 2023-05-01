import numpy as np
import argparse

from rtlsdr import RtlSdr

from adbs_decode_bits import adbs_decode_bits


BUFFER_SIZE = 256 * 1024 # 256K IQ samples

ADBS_PREAMBLE_SYM = 16
ADBS_MSG_LEN_BITS = 112
ADBS_MSG_LEN_SYM = ADBS_MSG_LEN_BITS*2
ADBS_PACKET_LEN_SYM = ADBS_PREAMBLE_SYM + ADBS_MSG_LEN_SYM


def demodulate_iq(iq_data: np.ndarray) -> np.ndarray:
    """
    Convert IQ uint8 samples to int8 amplitude.
    """
    iq_data = iq_data.view(np.int8)
    iq_data -= 128

    signal_i = iq_data[::2]
    signal_q = iq_data[1::2]

    demod_signal = signal_i +1j*signal_q
    demod_signal = np.abs(demod_signal)

    return demod_signal


def decode_symbols(demod_signal: np.ndarray):
    """
    Looks for the preamble.
    Decodes the symbols to bits.
    Calls the bit parsing function with the bits.
    """
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
        # print(f"Preamble OK: {np.array2string(demod_signal[i:i+16], max_line_width=100, precision=2)}")

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
            continue

        ##### DECODE BITS #####
        stats += adbs_decode_bits(''.join(str(i) for i in adbs_message_b), filter_df=17)

    return stats


def read_from_file(total_samples_read):
    """
    Reads from an IQ rtlsdr like file.
    """
    iq_data = np.fromfile(filename, dtype=np.uint8, count=BUFFER_SIZE, offset=total_samples_read)
    total_samples_read += BUFFER_SIZE

    return iq_data, iq_data.size, total_samples_read


def read_from_rtlsdr(total_samples_read):
    """
    Reads from an rtlsdr device.
    """
    # TODO: Do it async
    iq_data = np.ctypeslib.as_array(sdr.read_bytes(BUFFER_SIZE))
    total_samples_read += BUFFER_SIZE
    read_size = BUFFER_SIZE

    return iq_data, read_size, total_samples_read


if __name__ == '__main__':

    #filename = 'recordings/896478_live.complex16u'  # 8d8964789909de8f30049352c619
    #filename = 'recordings/message.complex16u'  # 8f4d2023587790bba5998227c948
    #filename = 'recordings/usefull_to_compare.bin'

    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-r", "--rtl_sdr", help="Use a connected RTL SDR.", action="store_true")
    source.add_argument("-f", "--from_file", help="Use an RTL SDR like file. Provide filename.", type=str)
    args = parser.parse_args()

    demod_signal = np.zeros(BUFFER_SIZE//2 + ADBS_PACKET_LEN_SYM)
    read_new_samples = None

    total_samples_read = 0
    stats = 0

    if args.rtl_sdr:
        print("Using rtlsdr.")
        sdr = RtlSdr()
        sdr.sample_rate = 2e6
        sdr.center_freq = 1090e6
        sdr.gain = 'auto'
        read_new_samples = read_from_rtlsdr

    if filename:=args.from_file:
        print("Running from file.")
        print(f"File: {filename}")
        total_samples_read = 0
        read_new_samples = read_from_file

    while True:

        iq_data, read_size, total_samples_read = read_new_samples(total_samples_read)

        if read_size == 0:
            print("End of file.")
            break
            
        # Save first bits of the array for messages between 2 buffers
        demod_signal[ADBS_PACKET_LEN_SYM:ADBS_PACKET_LEN_SYM + read_size//2] = demodulate_iq(iq_data)

        stats += decode_symbols(demod_signal)

        # Save last un-iterated symbols at the begining of the array for the next iteration
        demod_signal[:ADBS_PACKET_LEN_SYM] = demod_signal[-ADBS_PACKET_LEN_SYM:]

    print(stats)
