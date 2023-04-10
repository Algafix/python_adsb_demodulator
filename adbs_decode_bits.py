from bitstring import BitArray

DownlinkFormat = {
    17 : 'ADS-B Message',
    18 : 'TIS-B Message'
}

Capability = {
    **dict.fromkeys(range(0,1), 'Level 1 Transponder'),
    **dict.fromkeys(range(1,4), 'Reserved'),
    **dict.fromkeys(range(4,5), 'Level 2+ Transponder w/ ability to CA 7 on-ground'),
    **dict.fromkeys(range(5,6), 'Level 2+ Transponder w/ ability to CA 7 airborne'),
    **dict.fromkeys(range(6,7), 'Level 2+ Transponder w/ ability to CA 7 in any case'),
    **dict.fromkeys(range(7,8), 'Downlink Request is 0 or Flight Status is 2, 3, 4, or 5'),
}

TypeCode = {
    **dict.fromkeys(range(1,5), 'Aircraft Identification'),
    **dict.fromkeys(range(5,9), 'Surface Position'),
    **dict.fromkeys(range(9,19), 'Airborne Position (w/ Baro Altitude)'),
    **dict.fromkeys(range(19,20), 'Airborne Velocities'),
    **dict.fromkeys(range(20,23), 'Airborne Position (w/ GNSS Height)'),
    **dict.fromkeys(range(23,28), 'Reserved'),
    **dict.fromkeys(range(28,29), 'Aircraft Status'),
    **dict.fromkeys(range(29,30), 'Target State and Status Information'),
    **dict.fromkeys(range(31,32), 'Aircraft Operation Status'),
}

CRC_GEN = BitArray(bin='1111111111111010000001001')

def validate_crc(message: BitArray):

    crc = message[-24:]
    message[-24:] = 0x000

    for i in range(len(message)-24):
        if message[i] == 1:
            message[i:i+25] = message[i:i+25] ^ CRC_GEN
    
    computed_crc = message[-24:]
    
    return crc == computed_crc


ERROR_MSG = 'Not in table!'


def adbs_decode_bits(bits: str, filter_df=False):

    data = BitArray(bin=''.join(bits))

    df = data[0:5].uint
    ca = data[5:8].uint
    icao = data[8:32].hex
    me = data[32:88]
    crc = data[88:112]

    if filter_df and filter_df != df:
        return 0

    print(f"\n[+] Raw hex message: {data.hex}")

    print(f"""
    \tDF: {df}\t\t{DownlinkFormat.get(df, ERROR_MSG)}
    \tCA: {ca}\t\t{Capability.get(ca, ERROR_MSG)}
    \tICAO: {icao}
    \tCRC: {crc}\t{'OK!' if validate_crc(data) else 'FAIL!'}""")

    tc = me[0:5].uint

    print(f"""
    \tMessage: {me}
    \t\tType Code: {tc}\t\t{TypeCode.get(tc, ERROR_MSG)}""")

    return 1

if __name__ == '__main__':
    #symbols = '101000010100000010010101101001101001010110010110011010010110010101101010100101011001011010010110010101011001011010100110101010011001010110101010010110100101010101010101011001011001011001011010011001100101100110100101011010010101011010010110'
    #adbs_decode_bits(symbols)
    pass
