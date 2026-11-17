"""Lista elementos clicáveis sem interagir."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_agent import Device
device=Device(); device.wake_unlock()
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")
for n in device.dump():
    if n.clickable: print(f"text={n.text!r} desc={n.desc!r} id={n.rid!r} bounds={n.bounds}")
