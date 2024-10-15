"""
Mind Monitor - EEG OSC Receiver
Coded: James Clutterbuck (2022)
Requires: pip install python-osc
"""
from datetime import datetime
from pythonosc import dispatcher
from pythonosc import osc_server
import platform
import threading

class OscServer:
    def __init__(self, ip="127.0.0.1", port=5000):
        self.ip = ip
        self.port = port
        self.auxCount = -1
        self.recording = False

        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.filePath = 'OSC-Data.csv'
        else:
            self.filePath = '/storage/emulated/0/Download/OSC-Data.csv'

        self.f = open(self.filePath, 'w+')
        self.writeFileHeader()
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/muse/eeg", self.eeg_handler)
        self.dispatcher.map("/Marker/*", self.marker_handler)

        self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)

    def writeFileHeader(self):
        fileString = 'TimeStamp,RAW_TP9,RAW_AF7,RAW_AF8,RAW_TP10,'
        for x in range(0, self.auxCount):
            fileString += 'AUX' + str(x + 1) + ','
        fileString += 'Marker\n'
        self.f.write(fileString)

    def eeg_handler(self, address: str, *args):
        if self.auxCount == -1:
            self.auxCount = len(args) - 4
            self.writeFileHeader()
        if self.recording:
            timestampStr = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            fileString = timestampStr
            for arg in args:
                fileString += "," + str(arg)
            fileString += "\n"
            self.f.write(fileString)

    def marker_handler(self, address: str, i):
        timestampStr = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        markerNum = address[-1]
        if self.recording:
            fileString = timestampStr + ',,,,,' 
            for x in range(0, self.auxCount):
                fileString += ','
            fileString += '/Marker/' + markerNum + "\n"
            self.f.write(fileString)
        if markerNum == "1":
            self.recording = True
            print("Recording Started.")
        if markerNum == "5":
            self.f.close()
            self.recording = False
            self.server.shutdown()
            print("Recording Stopped.")

    def start(self):
        """Start the OSC server."""
        print(f"Starting OSC Server on {self.ip}:{self.port}...")
        threading.Thread(target=self.server.serve_forever).start()

if __name__ == "__main__":
    osc_server_instance = OscServer()
    osc_server_instance.start()
