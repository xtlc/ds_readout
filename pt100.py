
sensor 1

/sys/devices/w1_bus_master1/28-0000006a2c70 $ cat w1_slave 
4c 01 7f 80 7f ff 04 10 7a : crc=7a YES
4c 01 7f 80 7f ff 04 10 7a t=20750


sensor 2

rabaton@raspberrypi:/sys/bus/w1/devices $ ls -la
insgesamt 0
drwxr-xr-x 2 root root 0  4. Dez 12:06 .
drwxr-xr-x 4 root root 0  4. Dez 12:03 ..
lrwxrwxrwx 1 root root 0  4. Dez 12:46 28-0000006a2c70 -> ../../../devices/w1_bus_master1/28-0000006a2c70
lrwxrwxrwx 1 root root 0  4. Dez 12:46 28-0000006ada1a -> ../../../devices/w1_bus_master1/28-0000006ada1a
lrwxrwxrwx 1 root root 0  4. Dez 12:06 w1_bus_master1 -> ../../../devices/w1_bus_master1
rabaton@raspberrypi:/sys/bus/w1/devices $ cd 28-0000006ada1a/
rabaton@raspberrypi:/sys/bus/w1/devices/28-0000006ada1a $ cat w1_slave 
51 01 7f 80 7f ff 0f 10 71 : crc=71 YES
51 01 7f 80 7f ff 0f 10 71 t=21062
