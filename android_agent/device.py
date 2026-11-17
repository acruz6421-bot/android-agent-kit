"""Controle de dispositivos Android por ADB, com seletores sem coordenadas fixas."""
from __future__ import annotations
import base64, hashlib, html, os, random, re, shutil, subprocess, tempfile, threading, time
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

_IME_ADB = "com.android.adbkeyboard/.AdbIME"
_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()

@contextmanager
def _serial_file_lock(serial: str):
    """Serializa comandos entre processos que compartilham o mesmo aparelho."""
    token = hashlib.sha256(serial.encode("utf-8")).hexdigest()
    lock_path = Path(tempfile.gettempdir()) / f"android_agent_{token}.lock"
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

@dataclass
class Node:
    """Elemento da interface extraído do XML de acessibilidade."""
    text: str
    desc: str
    rid: str
    bounds: tuple[int, int, int, int] | None
    clickable: bool
    @property
    def center(self) -> tuple[int, int] | None:
        """Centro calculado a partir dos limites fornecidos pelo Android."""
        if not self.bounds: return None
        x1, y1, x2, y2 = self.bounds
        return ((x1+x2)//2, (y1+y2)//2)

class Device:
    """Interface Android que usa ADB e apenas a biblioteca padrão."""
    def __init__(self, serial: str | None = None, adb_path: str = "adb",
                 command_timeout: float = 20.0) -> None:
        env_serial = os.getenv("ANDROID_SERIAL") or ""
        if not env_serial:
            env_file = Path.cwd() / ".env"
            if env_file.is_file():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    key, separator, value = line.partition("=")
                    if separator and key.strip() == "ANDROID_SERIAL":
                        env_serial = value.strip().strip('"').strip("'")
                        break
        self.serial = (serial or env_serial).strip()
        if not self.serial: raise ValueError("Informe serial ou defina ANDROID_SERIAL.")
        self.adb_path = shutil.which(adb_path) or adb_path
        self.command_timeout = command_timeout
        with _LOCKS_GUARD: self._lock = _LOCKS.setdefault(self.serial, threading.RLock())

    def adb(self, *args: str, timeout: float | None = None, check: bool = True) -> str:
        """Executa ADB para este serial e devolve a saída textual."""
        cmd = [self.adb_path, "-s", self.serial, *map(str, args)]
        with self._lock, _serial_file_lock(self.serial):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=timeout or self.command_timeout)
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(f"ADB excedeu o prazo: {' '.join(cmd)}") from exc
        output = (result.stdout or "").strip()
        if check and result.returncode:
            raise RuntimeError((result.stderr or output or "Falha no ADB").strip())
        return output

    def human_pause(self, minimum: float = 0.4, maximum: float = 1.2) -> float:
        """Aguarda intervalo aleatório entre ações."""
        if minimum < 0 or maximum < minimum: raise ValueError("Intervalo de pausa inválido.")
        delay = random.uniform(minimum, maximum); time.sleep(delay); return delay

    def wake_unlock(self) -> bool:
        """Acorda a tela e tenta somente arrastar; nunca digita PIN."""
        self.adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        self.human_pause(0.4, 0.8)
        window = self.adb("shell", "dumpsys", "window", check=False)
        if not re.search(r"isKeyguardShowing=true|mDreamingLockscreen=true", window): return True
        size = self.adb("shell", "wm", "size", check=False)
        match = re.search(r"(\d+)x(\d+)", size)
        width, height = map(int, match.groups()) if match else (1080, 2400)
        x = width // 2
        self.adb("shell", "input", "swipe", str(x), str(int(height*.88)), str(x), str(int(height*.18)), "350")
        self.human_pause(0.7, 1.1)
        window = self.adb("shell", "dumpsys", "window", check=False)
        if re.search(r"isKeyguardShowing=true|mDreamingLockscreen=true", window):
            raise RuntimeError("Tela bloqueada. Desbloqueie manualmente; nenhum PIN foi tentado.")
        return True

    @staticmethod
    def _parse_bounds(value: str) -> tuple[int, int, int, int] | None:
        m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", value or "")
        return tuple(map(int, m.groups())) if m else None

    def dump(self, timeout: float = 15.0) -> list[Node]:
        """Obtém hierarquia UIAutomator com prazo e converte nós."""
        remote = "/sdcard/window_dump.xml"; xml_text = ""
        for attempt in range(2):
            self.adb("shell", "uiautomator", "dump", remote, timeout=timeout, check=False)
            xml_text = self.adb("shell", "cat", remote, timeout=8, check=False)
            if "<hierarchy" in xml_text: break
            if attempt == 0: self.human_pause(0.8, 1.4)
        if "<hierarchy" not in xml_text: return []
        try: root = ET.fromstring(xml_text[xml_text.find("<hierarchy"):])
        except ET.ParseError: return []
        nodes=[]
        for element in root.iter("node"):
            a=element.attrib
            nodes.append(Node(html.unescape(a.get("text","")), html.unescape(a.get("content-desc","")),
                a.get("resource-id","").rsplit("/",1)[-1], self._parse_bounds(a.get("bounds","")),
                a.get("clickable","false").lower()=="true"))
        return nodes

    def find(self, text: str | None = None, desc: str | None = None,
             rid: str | None = None, contains: bool = True) -> list[Node]:
        """Busca nós por texto, descrição ou ID, com correspondência parcial opcional."""
        if not any(v is not None for v in (text,desc,rid)): raise ValueError("Informe text, desc ou rid.")
        found=[]
        for node in self.dump():
            checks=[]
            for expected, actual in ((text,node.text),(desc,node.desc),(rid,node.rid)):
                if expected is not None:
                    checks.append(expected.casefold() in actual.casefold() if contains
                                  else expected.casefold()==actual.casefold())
            if any(checks): found.append(node)
        return found

    def tap(self, node: Node | str) -> Node:
        """Toca no centro dos bounds de um nó; texto é resolvido pela hierarquia atual."""
        candidates=self.find(text=node) if isinstance(node,str) else [node]
        target=next((n for n in candidates if n.bounds),None)
        if target is None or target.center is None: raise LookupError(f"Elemento sem bounds ou ausente: {node!r}")
        x,y=target.center; self.adb("shell","input","tap",str(x),str(y))
        self.human_pause(.25,.65); return target

    def type_text(self, value: str) -> None:
        """Digita UTF-8 via ADBKeyBoard instalado; restaura o teclado anterior ao terminar."""
        encoded=base64.b64encode(value.encode("utf-8")).decode("ascii")
        all_imes=self.adb("shell","ime","list","-a",check=False)
        if _IME_ADB in all_imes:
            previous=self.adb("shell","settings","get","secure","default_input_method",check=False)
            self.adb("shell","ime","enable",_IME_ADB,check=False)
            self.adb("shell","ime","set",_IME_ADB,check=False)
            try:
                self.adb("shell","am","broadcast","-a","ADB_INPUT_B64","--es","msg",encoded,check=False)
                self.human_pause(.3,.7)
            finally:
                if previous and previous != "null" and previous != _IME_ADB:
                    self.adb("shell","ime","set",previous,check=False)
            return
        safe=value.replace("%","%25").replace(" ","%s")
        safe=re.sub(r"([&<>|;()$\\\"'])", r"\\\1", safe)
        self.adb("shell","input","text",safe)

    def _swipe_vertical(self, start: float, end: float) -> None:
        """Executa gesto proporcional às dimensões atuais informadas pelo Android."""
        size=self.adb("shell","wm","size",check=False); m=re.search(r"(\d+)x(\d+)",size)
        width,height=map(int,m.groups()) if m else (1080,2400); x=width//2
        self.adb("shell","input","swipe",str(x),str(int(height*start)),str(x),str(int(height*end)),"450")
        self.human_pause(.35,.8)
    def swipe_up(self) -> None:
        """Rola para cima."""; self._swipe_vertical(.78,.28)
    def swipe_down(self) -> None:
        """Rola para baixo."""; self._swipe_vertical(.28,.78)
    def back(self) -> None:
        """Aciona voltar."""; self.adb("shell","input","keyevent","KEYCODE_BACK"); self.human_pause(.3,.7)
    def home(self) -> None:
        """Vai para a tela inicial."""; self.adb("shell","input","keyevent","KEYCODE_HOME"); self.human_pause(.3,.7)
    def open_url(self, url: str, package: str | None = None) -> None:
        """Abre URL por intent VIEW, opcionalmente restringindo ao pacote."""
        if urlparse(url).scheme not in {"http","https","mailto","tel","geo"}: raise ValueError("Esquema de URL não permitido.")
        args=["shell","am","start","-a","android.intent.action.VIEW","-d",url]
        if package: args += ["-p", package]
        self.adb(*args); self.human_pause(1,2)
    def screenshot(self, path: str | Path) -> Path:
        """Captura a tela e salva a imagem no caminho local."""
        destination=Path(path); destination.parent.mkdir(parents=True,exist_ok=True)
        remote="/sdcard/android_agent_shot.png"
        self.adb("shell","screencap","-p",remote); self.adb("pull",remote,str(destination))
        return destination
