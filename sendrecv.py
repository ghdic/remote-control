import struct

class SendRecv:
    def __init__(self, sock):
        self.sock = sock
    def send(self, data):
        pkt = struct.pack('>I', len(data)) + data
        self.sock.sendall(pkt)

    def recv(self):
        pktlen = self.recvall(4)
        if not pktlen: return ""
        pktlen = struct.unpack('>I', pktlen)[0] # >의미는 빅엔디안(넼웤 통신)
        return self.recvall(pktlen)

    def recvall(self, n):
        packet = b''
        while len(packet) < n:
            frame = self.sock.recv(n - len(packet))
            if not frame: return None
            packet += frame
        return packet