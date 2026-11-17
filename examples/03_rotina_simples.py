"""Abre um pacote, percorre a tela cinco vezes e retorna ao início."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sys
from android_agent import Device
if len(sys.argv)<2: raise SystemExit("Uso: python examples/03_rotina_simples.py nome.do.pacote")
device=Device(); device.wake_unlock()
device.adb("shell","monkey","-p",sys.argv[1],"1")
device.human_pause(2,3.5)
for _ in range(5):
    device.swipe_up(); device.human_pause(1,2.4)
device.home()
