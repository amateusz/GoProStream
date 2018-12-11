## GoPro Instant Streaming v1.0_r1
##
## By @Sonof8Bits and @KonradIT
##
## WOL touch by @5perseo, code updated by @podfish
##
## 1. Connect your desktop or laptop to your GoPro via WIFI.
## 2. Set the parameters below.
## 3. Run this script.
##
## Supported cameras:
## GoPro HERO5 (incl. Session), HERO4 (incl. Session), HERO+, HERO3+, HERO3, HERO2 w/ WiFi BacPac, HERO 2018.
##
## That's all! When done, press CTRL+C to quit this application.
## 

import sys
import socket

# from urllib.request import urlopen --> module import error
# https://stackoverflow.com/questions/2792650/python3-error-import-error-no-module-name-urllib2

# try:
# For Python 3.0 and later
from urllib.request import urlopen
# except ImportError:
# Fall back to Python 2's urllib2
# from urllib2 import urlopen

import subprocess
from time import sleep
import signal
import json
import re
import http

# GOPRO_IP = '10.5.5.9'
GOPRO_IP = 'aadbcd9c-66c2-477d-a652-0f9810819317.mock.pstmn.io'

UDP_IP = GOPRO_IP
UDP_PORT = 8554

## Parameters:
##
VERBOSE = True
## Sends Record command to GoPro Camera, must be in Video mode!
RECORD = False
## Saves the feed to a custom location
SAVE = False
## Open the stream and shows the preview
PREVIEW = False

SAVE_FILENAME = "goprofeed3"
SAVE_FORMAT = "ts"
SAVE_LOCATION = "/tmp/"


class GoPro():
    KEEP_ALIVE_PERIOD = 2500  # ms
    KEEP_ALIVE_COMMAND = 2
    GOPRO_MAC = 'DEADBEEF0000'

    def __init__(self, ip, udp_port):
        signal.signal(signal.SIGINT, self.quit)

        self.IP, self.UDP_port = (ip, udp_port)
        self.setup_keepalive()

    def connect(self):
        """
        setup all IP/netowrk/connection related things. better call this after checking for presence
        :return:
        """
        self.UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.wake_on_lan()
        self.model_id, self.model_name = self.detect_model()
        self.init_stream()

    def present(self):
        """

        :return: Wheather there is a camera on the network
        """

        # ping it first. then maybe do some advanced tests
        present = False and ping(self.IP)
        if present:
            return True
        else:
            # try something different
            if self.update_status():
                return True
        return False

    def detect_model(self, response_raw=None):
        """
        Tries to determine camera model from firmware string
        :param firmware_string: obtained from JSON from http://10.5.5.9/gp/gpControl endpoint
        :return: a tuple with first few characters of a firmware string. e.g. HD4, HD3.22 and also the nice model name e.g. HERO 6 Session; it's messy. In case of HERO3/+ returns the whole firmware_string for compatibility
        """
        if response_raw:
            jsondata = json.loads(response_raw)
            firmware_string = jsondata["info"]["firmware_version"]
        else:
            try:
                # original code - response_raw = urllib.request.urlopen('http://10.5.5.9/gp/gpControl').read().decode('utf-8')
                response_raw = urlopen(f'http://{GOPRO_IP}/gp/gpControl').read().decode('utf-8')
                jsondata = json.loads(response_raw)
                firmware_string = jsondata["info"]["firmware_version"]
            except http.client.BadStatusLine:
                firmware_string = urlopen(f'http://{GOPRO_IP}/camera/cv').read().decode('utf-8')

        model_name = jsondata["info"]["model_name"]

        if "Hero3" in firmware_string or "HERO3+" in firmware_string:
            # HERO3 branch
            model_id = firmware_string
        else:
            model_id, *numbers = firmware_string.split('.')
            if len(numbers) == 3:
                model_id = '.'.join([model_id, numbers[0]])
        return (model_id, model_name)

    def open_stream(self):
        ##
        ## Opens the stream over udp in ffplay. This is a known working configuration by Reddit user hoppjerka:
        ## https://www.reddit.com/r/gopro/comments/2md8hm/how_to_livestream_from_a_gopro_hero4/cr1b193
        ##
        loglevel_verbose = ""
        if VERBOSE == False:
            loglevel_verbose = "-loglevel panic"
        if SAVE == True:
            if SAVE_FORMAT == "ts":
                TS_PARAMS = " -acodec copy -vcodec copy "
            else:
                TS_PARAMS = ""
            SAVELOCATION = SAVE_LOCATION + SAVE_FILENAME + "." + SAVE_FORMAT
            print("Recording locally: " + str(SAVE))
            print("Recording stored in: " + SAVELOCATION)
            print("Note: Preview is not available when saving the stream.")
            subprocess.Popen(
                f"ffmpeg -i 'udp://@:{UDP_PORT}' -fflags nobuffer -f:v mpegts -probesize 8192 " + TS_PARAMS + SAVELOCATION,
                shell=True)
        else:
            subprocess.Popen(
                f"ffplay {loglevel_verbose} -fflags nobuffer -f:v mpegts -probesize 8192 udp://@:{UDP_PORT}",
                shell=True)
            '''
            the meaning of above `@` is as explained in https://superuser.com/questions/870831/what-does-the-at-symbol-with-ips-mean-in-ffmpeg-and-vlc
            It turns of our UDP is multicast..or unicast, therefore where udp://x@y:8554 y makes no difference. x is our IP, most likely 10.5.5.100
            '''

        print("Press ctrl+C to quit this application.\n")

    def init_stream(self):
        if self.model_id == "HD4" or self.model_id == "HD3.22" or self.model_id == "HD5" or self.model_id == "HD6" or self.model_id == "H18" or "HX" in self.model_id:
            print("branch HD4")
            print(f'model: {self.model_name}')
            ##
            ## HTTP GETs the URL that tells the GoPro to start streaming.
            ##
            urlopen(f"http://{GOPRO_IP}/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart").read()
            if RECORD:
                # send /record/ command. saves the file locally onto the camera
                urlopen(f"http://{GOPRO_IP}/gp/gpControl/command/shutter?p=1").read()
            print("UDP target IP:", UDP_IP)
            print("UDP target port:", UDP_PORT)
            print("Recording on camera: " + str(RECORD))

            ## GoPro HERO4 Session needs status 31 to be greater or equal than 1 in order to start the live feed.
            ## https: // github.com / KonradIT / goprowifihack / blob / c4ecccc74b5a23ec13f2e2d214bb2ebbbda58f3c / HERO4 / HERO4 - Session.md
            if "HX" in self.model_id:
                connectedStatus = False
                while connectedStatus == False:
                    self.update_status()
                    if self.get_status_json()["status"]["31"] >= 1:
                        connectedStatus = True

        else:
            print("branch hero3 " + self.model_id)
            PRE_UDP_URL = f"http://{GOPRO_IP}:8080/live/amba.m3u8"  # only for pre-UDP HERO2, HERO3 and HERO3+

            if "Hero3" in self.model_id or "HERO3+" in self.model_id:
                print("branch hero3")
                PASSWORD = urlopen(f"http://{GOPRO_IP}/bacpac/sd").read()
                print("HERO3/3+/2 camera")
                Password = str(PASSWORD, 'utf-8')
                text = re.sub(r'\W+', '', Password)
                urlopen(f"http://{GOPRO_IP}/camera/PV?t=" + text + "&p=%02")
                subprocess.Popen("ffplay " + PRE_UDP_URL, shell=True)

    @staticmethod
    def get_command_msg(command):
        return "_GPHD_:%u:%u:%d:%1lf\n" % (0, 0, command, 0)

    def setup_keepalive(self):
        self.keep_alive_message = __class__.get_command_msg(__class__.KEEP_ALIVE_COMMAND)
        if sys.version_info.major >= 3:
            self.keep_alive_message = bytes(self.keep_alive_message, "utf-8")

    def keep_alive(self):
        """
        Some (?) cameras need a refresh packet, otherwise they will shutdown the live stream (being a preview really)
        based on: https://gist.github.com/3v1n0/38bcd4f7f0cb3c279bad#file-hero4-udp-keep-alive-send-py
        send UDP packet mimicking the original app
        """
        self.UDP_socket.sendto(self.keep_alive_message, (self.IP, self.UDP_port))
        sleep(__class__.KEEP_ALIVE_PERIOD / 1000)

    def wake_on_lan(self):
        """switches on remote computers using WoL"""

        # check macaddress format and try to compensate
        if len(__class__.GOPRO_MAC) == 12:
            macaddress = __class__.GOPRO_MAC
        elif len(__class__.GOPRO_MAC) == 12 + 5:
            sep = __class__.GOPRO_MAC[2]  # determine what separator is used
            macaddress = __class__.GOPRO_MAC.replace(sep, '')  # purge them
        else:
            raise ValueError('Incorrect MAC Address Format')
        # Pad the sync stream
        data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
        send_data = bytes.fromhex(data)

        # Broadcast to lan

        self.UDP_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.UDP_socket.sendto(send_data, (GOPRO_IP, 9))

    def update_status(self):
        try:
            req = urlopen(f"http://{GOPRO_IP}/gp/gpControl/status")
            data = req.read()
            encoding = req.info().get_content_charset('utf-8')
            self.status_json = json.loads(data.decode(encoding))
            return True
        except:
            return False

    def get_status_json(self):
        try:
            return self.status_json
        except AttributeError:
            return None

    def quit(self, signal, frame):
        if RECORD:
            # stop the shutter when closing
            urlopen(f"http://{GOPRO_IP}/gp/gpControl/command/shutter?p=0").read()
        sys.exit(0)


# https://stackoverflow.com/questions/2953462/pinging-servers-in-python
def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    from platform import system as system_name  # Returns the system/OS name
    from subprocess import call as system_call  # Execute a shell command
    from os import devnull

    # Ping command count option as function of OS
    param = '-n' if system_name().lower() == 'windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    # Pinging
    with open(devnull, "w") as devnull_f:
        result = system_call(command, stdout=devnull_f)
    return result == 0


if __name__ == '__main__':
    gopro = GoPro(UDP_IP, UDP_PORT)
    print('present') if gopro.present() else print('not present')
    gopro.connect()
    if PREVIEW:
        gopro.open_stream()

    while True:
        gopro.keep_alive()
