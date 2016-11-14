#!/usr/bin/python
import subprocess


def WLAN_check():
    '''
    This function checks if the WLAN is still up by pinging the router.
    If there is no return, we'll reset the WLAN connection.
    If the resetting of the WLAN does not work, we need to reset the Pi.
    '''

    flag = False
    for i in xrange(0, 2):
        loop(flag)
    return flag


def loop(WLAN_check_flg):
    ping_cmd = (
        'ping -c 2 -w 1 -q 192.168.1.1 | grep "1 received" > '
        '/dev/null 2> /dev/null'
    )
    ping_ret = subprocess.call([ping_cmd],
                               shell=True)
    if ping_ret:
        # we lost the WLAN connection.
        # did we try a recovery already?
        if WLAN_check_flg:
            # we have a serious problem and need to reboot
            # the Pi to recover the WLAN connection
            subprocess.call(['logger "WLAN down - Pi forcing reboot"'],
                            shell=True)
            WLAN_check_flg = False
            subprocess.call(['sudo reboot'],
                            shell=True)
        else:
            # try to recover the connection by resetting the LAN
            subprocess.call(['logger "WLAN down - Pi resetting WLAN"'],
                            shell=True)
            WLAN_check_flg = True  # try to recover
            subprocess.call([('sudo /sbin/ifdown wlan0 && sleep 10 && '
                              'sudo /sbin/ifup --force wlan0')],
                            shell=True)
    else:
        WLAN_check_flg = False

    return WLAN_check_flg

if __name__ == "__main__":
    WLAN_check()