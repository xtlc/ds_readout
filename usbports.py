import serial.tools.list_ports


def get_port(devicetype):
    """
    hand "temp" or "scale" to the function and receive the usb port address in return or None for error
    """
    ports = serial.tools.list_ports.comports()

    for port, desc, hwid in sorted(ports):
        if devicetype == "scale".casefold():
            if "RS485_Scales" in desc:
                return port
        elif devicetype == "temp".casefold():
            if "RS485_Temps" in desc:
                return port
    return None
