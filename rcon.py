"""EKB SHIELD — минимальный RCON-клиент для управления сервером с Windows.

На Linux скрипты слали команды через screen; на Windows окно сервера так не
подцепить, поэтому используется штатный RCON-протокол Minecraft.

Требует в server.properties:
    enable-rcon=true
    rcon.port=25575
    rcon.password=<пароль>

Использование:
    py -3 rcon.py "worldborder get"
    py -3 rcon.py "save-off" "save-all flush"
"""
import socket, struct, sys, pathlib, re

SERVER_DIR = pathlib.Path(r"D:\EKB_Shield\server")

def read_props():
    props = {}
    f = SERVER_DIR / "server.properties"
    for line in f.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            props[k.strip()] = v.strip()
    return props

class Rcon:
    def __init__(self, host, port, password):
        self.sock = socket.create_connection((host, port), timeout=10)
        self._send(3, password)          # 3 = аутентификация
        rid, _ = self._recv()
        if rid == -1:
            raise SystemExit("RCON: неверный пароль (rcon.password в server.properties)")

    def _send(self, type_, body):
        payload = struct.pack("<ii", 0, type_) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(payload)) + payload)

    def _recv(self):
        length = struct.unpack("<i", self.sock.recv(4))[0]
        data = b""
        while len(data) < length:
            data += self.sock.recv(length - len(data))
        rid, _type = struct.unpack("<ii", data[:8])
        return rid, data[8:-2].decode("utf-8", "replace")

    def command(self, cmd):
        self._send(2, cmd)               # 2 = команда
        _, body = self._recv()
        return re.sub(r"\x1b\[[0-9;]*m", "", body)   # убираем цветовые коды

    def close(self):
        self.sock.close()

def connect():
    p = read_props()
    if p.get("enable-rcon", "false").lower() != "true":
        raise SystemExit("RCON выключен. В server.properties: enable-rcon=true, rcon.password=<пароль>, затем перезапусти сервер.")
    pwd = p.get("rcon.password", "")
    if not pwd:
        raise SystemExit("rcon.password пуст — задай пароль в server.properties.")
    return Rcon("127.0.0.1", int(p.get("rcon.port", 25575)), pwd)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    # --file <путь>: команды построчно. Нужен для PowerShell — он ломает
    # аргументы с пробелами и кавычками при вызове exe (tellraw/title с JSON).
    if sys.argv[1] == "--file":
        cmds = [l.strip() for l in pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        cmds = sys.argv[1:]
    r = connect()
    for cmd in cmds:
        out = r.command(cmd)
        print(f"> {cmd}")
        if out.strip():
            print(f"  {out.strip()}")
    r.close()
