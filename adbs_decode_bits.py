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

def tc19(message: BitArray):

    subtype = message[5:8]

    vrate_source = message[35]


    pass



def adbs_decode_bits(bits: str, filter_df=False):

    data = BitArray(bin=''.join(bits))

    df = data[0:5].uint
    ca = data[5:8].uint
    icao = data[8:32].hex
    me = data[32:88]
    crc = data[88:112]

    crc_ok = validate_crc(BitArray(data))

    if not crc_ok:
        return 0

    if filter_df and filter_df != df:
        return 0

    tc = me[0:5].uint



    info_message = f"""
[+] Raw hex message: {data.hex}
    DF: {df}\t\t{DownlinkFormat.get(df, ERROR_MSG)}
    CA: {ca}\t\t{Capability.get(ca, ERROR_MSG)}
    ICAO: {icao}
    CRC: {crc}\t{'OK!' if crc_ok else 'FAIL!'}

    Message: {me}
        Type Code: {tc}\t\t{TypeCode.get(tc, ERROR_MSG)}
    """

    print(info_message)

    return 1

if __name__ == '__main__':
    pass
