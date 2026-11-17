"""CLI para inspecionar e controlar uma tela Android."""
import argparse
from .device import Device

def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")
    parser=argparse.ArgumentParser(description="Inspeciona Android via ADB.")
    sub=parser.add_subparsers(dest="action")
    sub.add_parser("dump",help="lista elementos")
    tap=sub.add_parser("tap",help="toca pelo texto"); tap.add_argument("text")
    key=sub.add_parser("key",help="envia tecla"); key.add_argument("keycode")
    shot=sub.add_parser("shot",help="captura tela"); shot.add_argument("path")
    args=parser.parse_args(); device=Device()
    if args.action in (None,"dump"):
        for n in device.dump():
            if n.text or n.desc or n.rid:
                print(f"text={n.text!r} desc={n.desc!r} id={n.rid!r} clickable={n.clickable} bounds={n.bounds}")
    elif args.action=="tap": device.tap(args.text)
    elif args.action=="key": device.adb("shell","input","keyevent",args.keycode)
    elif args.action=="shot": print(device.screenshot(args.path))
if __name__=="__main__": main()
