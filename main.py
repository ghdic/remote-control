from server import Server
from gui import Window
from PyQt5.QtWidgets import QApplication

class Manager:
    def __init__(self, host_ip, host_port):
        self.server = Server(host_ip, host_port)
        App = QApplication(sys.argv)
        self.window = Window()
        sys.exit(App.exec())