import argparse
import subprocess


class Restart:
    PI = "Raspberry Pi"
    IFACE = "LAN Interface"


def parse_args():
    """
    Set up an argument parser and return the parsed arguments
    @return: Result of calling parse_args() on the argparse.ArgumentParser object
    @rtype: argparse.Namespace
    """
    description = "Simple script to check connectivity and attempt to " \
                  "recover in case no connection is made"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--address",
        "-a",
        default="192.168.1.18",
        type=str,
        help="Address to ping for connection test"
    )
    parser.add_argument(
        "--interface",
        "-i",
        default="wlan0",
        type=str,
        help="LAN interface to restart as first attempt at recovering"
    )
    parser.add_argument(
        "--reboot",
        "-r",
        action="store_true",
        help="Flag to reboot the Pi if no connection"
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Debug mode - execute but don't actually do anything"
    )
    return parser.parse_args()


def wlan_check(address, interface, reboot=False, debug=False):
    """
    This function checks if the WLAN is still up by pinging the target address
    @param address: target address to ping
    @type address: str
    @param interface: target LAN interface
    @type interface: str
    @param reboot: Flag to enable rebooting. Default: False (disable reboot)
    @type reboot: bool
    @param debug: debug flag - doesn't actually do anything if debug is enabled
    @type debug: bool
    """
    # First attempt - restart the target interface
    result = check_connection(address, interface, Restart.IFACE, debug)
    if result:
        print("Connection is up - exiting")
        return

    # Second attempt - restart Pi if reboot==True, otherwise try a second interface restart
    result = check_connection(address, interface, Restart.PI if reboot else Restart.IFACE, debug)
    if result:
        print("Connection is up - exiting")
        return


def restart_pi():
    """
    Restart the Pi as a last ditch effort
    """
    print("Restarting Pi!")
    subprocess.call(
        ['logger "WLAN down - Pi forcing reboot"'],
        shell=True
    )
    cmd = "sudo shutdown -r now"
    print(f"Executing command:\n\t{cmd}")
    subprocess.call([cmd], shell=True)


def restart_interface(interface):
    """
    Restart the specified LAN interface
    @param interface: target LAN interface
    @type interface: str
    """
    # try to recover the connection by resetting the LAN
    print(f"Attempting to restart '{interface}'...")
    subprocess.call(
        [f'logger "{interface} down - Pi resetting {interface}"'],
        shell=True
    )

    cmd = f"sudo /sbin/ifdown {interface} && sleep 10 && " \
          f"sudo /sbin/ifup --force {interface}"
    print(f"Executing command:\n\t{cmd}")
    subprocess.call(
        [cmd],
        shell=True
    )


def check_connection(ping_address, interface, restart_target=Restart.PI, debug=False):
    """
    Ping the address & either reboot the LAN interface
    @param ping_address: address to ping
    @type ping_address: str
    @param interface: target interface to reboot
    @type interface: str
    @param restart_target: Target for restarting
    @type restart_target: str
    @param debug: debug flag
    @type debug: bool
    @return: Result of ping - True if response received, False otherwise
    @rtype: bool
    """
    # This command pings the target address & looks for "1 received"
    # It will return 0 if the ping is successful, and non-zero if not
    ping_cmd = f'ping -c 2 -W 1 -q {ping_address} | grep "1 received" > /dev/null 2> /dev/null'
    response = subprocess.call([ping_cmd], shell=True)

    if response == 0:
        # Connection up - response was received
        return True

    else:
        # Connection down - response was non-zero
        if debug:
            print(f"Debug mode enabled - would restart {restart_target} otherwise!")
            return False

        if restart_target == Restart.IFACE:
            # Target is interface
            restart_interface(interface)
        elif restart_target == Restart.PI:
            # Target is pi
            restart_pi()
        else:
            raise Exception(f"Unrecognized restart target: {restart_target}")

        return False


if __name__ == "__main__":
    args = parse_args()
    print(
        f"Address: {args.address}\nInterface: {args.interface}\nDo not reboot: {not args.reboot}\nDebug: {args.debug}"
    )
    # wlan_check(args.address, args.interface, args.reboot, args.debug)
    wlan_check(**args.__dict__)
