"""Abre URL de demonstração e salva captura."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sys
from android_agent import Device
url=sys.argv[1] if len(sys.argv)>1 else "https://example.org"
device=Device(); device.wake_unlock(); device.open_url(url)
device.human_pause(4, 6)  # espera a página carregar antes do print
print(device.screenshot("shots/01_abrir_link.png"))
