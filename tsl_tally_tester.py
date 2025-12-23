#!/usr/bin/env python3
"""
TSL Tally Tester - Professional TSL 3.1 Tally Testing Tool
Version 1.0.0

A standalone utility for testing TSL tally systems.
Sends TSL 3.1 UDP packets to tally receivers/bridges.

Author: Fresh AV Labs
Website: https://www.freshavlabs.com
License: MIT
"""

import json
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import sys
import random

APP_NAME = "TSL Tally Tester"
APP_VERSION = "1.0.0"
CONFIG_FILE = "tsl_tester_config.json"

# Modern dark color scheme
C = {
    'bg': '#0f1419',
    'bg2': '#151b23',
    'bg3': '#1c2430',
    'card': '#212b3a',
    'border': '#2d3a4d',
    'accent': '#0ea5e9',
    'text': '#e2e8f0',
    'muted': '#64748b',
    'pgm': '#dc2626',
    'pgm_dim': '#7f1d1d',
    'pvw': '#16a34a',
    'pvw_dim': '#14532d',
    'both': '#d97706',
    'both_dim': '#78350f',
    'off': '#374151',
    'off_dim': '#1f2937',
    'success': '#22c55e',
    'error': '#ef4444',
}


class TSL31:
    """TSL 3.1 Protocol"""
    
    @staticmethod
    def packet(addr: int, pgm: bool, pvw: bool, label: str = "") -> bytes:
        ctrl = (0x01 if pgm else 0) | (0x02 if pvw else 0)
        lbl = label[:14].ljust(14).encode('ascii', errors='replace')
        return bytes([0x80, max(0, addr - 1), ctrl, 0x00]) + lbl
    
    @staticmethod
    def send(ip: str, port: int, pkt: bytes) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.3)
            s.sendto(pkt, (ip, port))
            s.close()
            return True
        except:
            return False


class TallyRow(tk.Frame):
    """Single input row"""
    
    def __init__(self, parent, num, callback):
        super().__init__(parent, bg=C['card'], pady=6, padx=10)
        self.num = num
        self.callback = callback
        self.state = 'off'
        
        # Number
        tk.Label(self, text=f"{num:2d}", font=('Consolas', 12, 'bold'),
                bg=C['card'], fg=C['muted'], width=3).pack(side='left')
        
        # Indicator bar
        self.ind = tk.Frame(self, width=4, height=28, bg=C['off'])
        self.ind.pack(side='left', padx=(8, 12))
        self.ind.pack_propagate(False)
        
        # Main button
        self.btn = tk.Button(self, text="OFF", width=6, font=('Segoe UI', 10, 'bold'),
                            bg=C['off'], fg='white', relief='flat', bd=0,
                            activebackground=C['off_dim'], cursor='hand2',
                            command=self._cycle)
        self.btn.pack(side='left', padx=2)
        
        # Quick buttons frame
        qf = tk.Frame(self, bg=C['card'])
        qf.pack(side='left', padx=8)
        
        for txt, st, col in [('P', 'pgm', C['pgm_dim']), ('V', 'pvw', C['pvw_dim']), ('X', 'off', C['off_dim'])]:
            b = tk.Button(qf, text=txt, width=2, font=('Segoe UI', 9, 'bold'),
                         bg=col, fg='white', relief='flat', bd=0, cursor='hand2',
                         command=lambda s=st: self.set_state(s))
            b.pack(side='left', padx=1)
        
        # Label
        self.label = tk.StringVar(value=f"CAM {num}")
        e = tk.Entry(self, textvariable=self.label, width=14, font=('Segoe UI', 10),
                    bg=C['bg3'], fg=C['text'], relief='flat', insertbackground=C['text'],
                    highlightthickness=1, highlightbackground=C['border'], highlightcolor=C['accent'])
        e.pack(side='left', padx=10, ipady=3)
        e.bind('<Return>', lambda e: self._send())
    
    def _cycle(self):
        states = ['off', 'pgm', 'pvw', 'both']
        self.set_state(states[(states.index(self.state) + 1) % 4])
    
    def set_state(self, st, send=True):
        self.state = st
        cfg = {
            'off': (C['off'], 'OFF'),
            'pgm': (C['pgm'], 'PGM'),
            'pvw': (C['pvw'], 'PVW'),
            'both': (C['both'], 'BOTH')
        }
        col, txt = cfg[st]
        self.btn.config(bg=col, text=txt, activebackground=col)
        self.ind.config(bg=col)
        if send:
            self._send()
    
    def _send(self):
        self.callback(self.num, self.state in ('pgm', 'both'), 
                     self.state in ('pvw', 'both'), self.label.get())
    
    def get_label(self):
        return self.label.get()
    
    def set_label(self, v):
        self.label.set(v)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("720x820")
        self.root.configure(bg=C['bg'])
        self.root.minsize(680, 600)
        
        self.ip = tk.StringVar(value="192.168.1.100")
        self.port = tk.StringVar(value="5727")
        self.inputs = {}
        self.packets = 0
        self.errors = 0
        self.running = {'demo': False, 'chase': False}
        self.enabled = False  # Start/stop state
        
        self._load_cfg()
        self._build()
        self._make_inputs()
        self._page(0)
    
    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C['bg2'], pady=12)
        hdr.pack(fill='x')
        
        # Title
        tf = tk.Frame(hdr, bg=C['bg2'])
        tf.pack(side='left', padx=20)
        tk.Label(tf, text="TSL", font=('Segoe UI', 22, 'bold'),
                bg=C['bg2'], fg=C['accent']).pack(side='left')
        tk.Label(tf, text=" Tally Tester", font=('Segoe UI', 22),
                bg=C['bg2'], fg=C['text']).pack(side='left')
        tk.Label(tf, text="  by Fresh AV Labs", font=('Segoe UI', 11),
                bg=C['bg2'], fg=C['muted']).pack(side='left', padx=(10, 0))
        
        # Connection
        cf = tk.Frame(hdr, bg=C['bg2'])
        cf.pack(side='left', padx=25)
        
        for lbl, var, w in [("IP Address", self.ip, 14), ("Port", self.port, 6)]:
            f = tk.Frame(cf, bg=C['bg2'])
            f.pack(side='left', padx=8)
            tk.Label(f, text=lbl, font=('Segoe UI', 8), bg=C['bg2'], fg=C['muted']).pack(anchor='w')
            tk.Entry(f, textvariable=var, width=w, font=('Segoe UI', 11),
                    bg=C['bg3'], fg=C['text'], relief='flat', insertbackground=C['text']).pack(ipady=3)
        
        # Start/Stop button
        self.start_btn = tk.Button(cf, text="START", font=('Segoe UI', 11, 'bold'), width=8,
                                   bg=C['pvw'], fg='white', relief='flat', cursor='hand2',
                                   activebackground=C['pvw_dim'], command=self._toggle_enabled)
        self.start_btn.pack(side='left', padx=(15, 0), ipady=4)
        
        # Stats
        sf = tk.Frame(hdr, bg=C['bg2'])
        sf.pack(side='right', padx=20)
        
        self.dot = tk.Label(sf, text="●", font=('Segoe UI', 16), bg=C['bg2'], fg=C['muted'])
        self.dot.pack(side='left')
        
        stf = tk.Frame(sf, bg=C['bg2'])
        stf.pack(side='left', padx=8)
        self.pkt_lbl = tk.Label(stf, text="0 sent", font=('Segoe UI', 10), bg=C['bg2'], fg=C['text'])
        self.pkt_lbl.pack(anchor='w')
        self.status_lbl = tk.Label(stf, text="Stopped", font=('Segoe UI', 9), bg=C['bg2'], fg=C['muted'])
        self.status_lbl.pack(anchor='w')
        
        # Actions
        act = tk.Frame(self.root, bg=C['bg3'], pady=10)
        act.pack(fill='x')
        
        af = tk.Frame(act, bg=C['bg3'])
        af.pack()
        
        btns = [
            ("All OFF", self._all_off, 'off'),
            ("Send Labels", self._send_labels, 'off'),
            ("Demo", lambda: self._toggle('demo'), 'demo'),
            ("Chase", lambda: self._toggle('chase'), 'chase'),
            ("Random", self._random, 'off'),
        ]
        self.action_btns = {}
        for txt, cmd, key in btns:
            b = tk.Button(af, text=txt, font=('Segoe UI', 9, 'bold'), width=10,
                     bg=C['off'], fg='white', relief='flat', cursor='hand2',
                     activebackground=C['off_dim'], command=cmd)
            b.pack(side='left', padx=3)
            if key in ('demo', 'chase'):
                self.action_btns[key] = b
        
        # Separator
        tk.Frame(af, width=1, height=24, bg=C['border']).pack(side='left', padx=12)
        
        # Presets
        tk.Label(af, text="Labels:", font=('Segoe UI', 9), bg=C['bg3'], fg=C['muted']).pack(side='left', padx=(0,5))
        self.preset = tk.StringVar(value="CAM #")
        ttk.Combobox(af, textvariable=self.preset, width=9, state='readonly',
                    values=["CAM #", "Camera #", "Input #", "Source #", "Clear"]).pack(side='left')
        tk.Button(af, text="Apply", font=('Segoe UI', 9), width=6, bg=C['off'], fg='white',
                 relief='flat', cursor='hand2', command=self._preset).pack(side='left', padx=5)
        
        # Page nav
        nav = tk.Frame(self.root, bg=C['bg'], pady=8)
        nav.pack(fill='x')
        
        nf = tk.Frame(nav, bg=C['bg'])
        nf.pack()
        
        self.pages = []
        for i in range(5):  # 80 inputs / 16 per page
            s, e = i*16+1, min((i+1)*16, 80)
            b = tk.Button(nf, text=f"{s}-{e}", font=('Segoe UI', 9), width=6,
                         bg=C['off'], fg='white', relief='flat', cursor='hand2',
                         command=lambda p=i: self._page(p))
            b.pack(side='left', padx=2)
            self.pages.append(b)
        
        # Input container
        container = tk.Frame(self.root, bg=C['bg'])
        container.pack(fill='both', expand=True, padx=12, pady=5)
        
        self.canvas = tk.Canvas(container, bg=C['bg'], highlightthickness=0)
        sb = ttk.Scrollbar(container, orient='vertical', command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas, bg=C['bg'])
        
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        self.win = self.canvas.create_window((0,0), window=self.frame, anchor='nw')
        self.frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.win, width=e.width))
        self.canvas.bind_all('<MouseWheel>', lambda e: self.canvas.yview_scroll(int(-e.delta/120), 'units'))
        
        # Footer
        ft = tk.Frame(self.root, bg=C['bg2'], pady=6)
        ft.pack(fill='x', side='bottom')
        
        tk.Label(ft, text="TSL 3.1 Protocol", font=('Segoe UI', 9),
                bg=C['bg2'], fg=C['muted']).pack(side='left', padx=15)
        
        bf = tk.Frame(ft, bg=C['bg2'])
        bf.pack(side='right', padx=15)
        
        for txt, cmd in [("Save", self._save), ("Load", self._load_dlg)]:
            tk.Button(bf, text=txt, font=('Segoe UI', 9), width=6, bg=C['off'], fg='white',
                     relief='flat', cursor='hand2', command=cmd).pack(side='left', padx=2)
        
        tk.Label(ft, text=f"v{APP_VERSION}", font=('Segoe UI', 9),
                bg=C['bg2'], fg=C['muted']).pack(side='right', padx=10)
    
    def _make_inputs(self):
        for i in range(1, 81):
            self.inputs[i] = TallyRow(self.frame, i, self._send)
        
        # Apply loaded labels
        if hasattr(self, '_labels'):
            for k, v in self._labels.items():
                if int(k) in self.inputs:
                    self.inputs[int(k)].set_label(v)
    
    def _page(self, p):
        self.cur_page = p
        for i, b in enumerate(self.pages):
            b.config(bg=C['accent'] if i == p else C['off'])
        
        for w in self.inputs.values():
            w.pack_forget()
        
        for i in range(p*16+1, min((p+1)*16+1, 81)):
            self.inputs[i].pack(fill='x', pady=2)
        
        self.canvas.yview_moveto(0)
    
    def _toggle_enabled(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.start_btn.config(text="STOP", bg=C['pgm'], activebackground=C['pgm_dim'])
            self.dot.config(fg=C['success'])
            self.status_lbl.config(text="Running", fg=C['success'])
        else:
            self.start_btn.config(text="START", bg=C['pvw'], activebackground=C['pvw_dim'])
            self.dot.config(fg=C['muted'])
            self.status_lbl.config(text="Stopped", fg=C['muted'])
            # Stop any running demos/chases
            self.running['demo'] = False
            self.running['chase'] = False
    
    def _send(self, num, pgm, pvw, label):
        if not self.enabled:
            return
        try:
            pkt = TSL31.packet(num, pgm, pvw, label)
            if TSL31.send(self.ip.get(), int(self.port.get()), pkt):
                self.packets += 1
                self._flash(C['success'])
            else:
                self.errors += 1
                self._flash(C['error'])
        except:
            self.errors += 1
            self._flash(C['error'])
        self._stats()
    
    def _flash(self, c):
        self.dot.config(fg=c)
        self.root.after(100, lambda: self.dot.config(fg=C['muted']))
    
    def _stats(self):
        self.pkt_lbl.config(text=f"{self.packets} sent")
    
    def _all_off(self):
        for w in self.inputs.values():
            w.set_state('off')
            time.sleep(0.003)
    
    def _send_labels(self):
        for w in self.inputs.values():
            w._send()
            time.sleep(0.003)
    
    def _toggle(self, mode):
        if self.running[mode]:
            self.running[mode] = False
            self.action_btns[mode].config(bg=C['off'], text=mode.title())
        else:
            if not self.enabled:
                return  # Don't start if not enabled
            self.running[mode] = True
            self.action_btns[mode].config(bg=C['accent'], text=f"{mode.title()} ON")
            threading.Thread(target=self._demo if mode == 'demo' else self._chase, daemon=True).start()
    
    def _demo(self):
        while self.running['demo']:
            for i in range(1, 9):
                if not self.running['demo']:
                    break
                for j in range(1, 9):
                    self.inputs[j].set_state('off')
                self.inputs[i].set_state('pgm')
                self.inputs[(i % 8) + 1].set_state('pvw')
                time.sleep(0.7)
        for j in range(1, 9):
            self.inputs[j].set_state('off')
        self.action_btns['demo'].config(bg=C['off'], text='Demo')
    
    def _chase(self):
        while self.running['chase']:
            for i in range(1, 81):
                if not self.running['chase']:
                    break
                self.inputs[i].set_state('pgm')
                time.sleep(1.0)
                self.inputs[i].set_state('off')
        self.action_btns['chase'].config(bg=C['off'], text='Chase')
    
    def _random(self):
        for w in self.inputs.values():
            w.set_state('off', send=False)
        p, v = random.sample(range(1, 81), 2)
        self.inputs[p].set_state('pgm')
        self.inputs[v].set_state('pvw')
    
    def _preset(self):
        pr = self.preset.get()
        for i, w in self.inputs.items():
            if pr == "Clear":
                w.set_label("")
            else:
                w.set_label(pr.replace("#", str(i)))
    
    def _save(self):
        cfg = {'ip': self.ip.get(), 'port': self.port.get(),
               'labels': {str(i): w.get_label() for i, w in self.inputs.items()}}
        p = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if p:
            with open(p, 'w') as f:
                json.dump(cfg, f, indent=2)
    
    def _load_cfg(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE) as f:
                    cfg = json.load(f)
                self.ip.set(cfg.get('ip', '192.168.1.100'))
                self.port.set(cfg.get('port', '5727'))
                self._labels = cfg.get('labels', {})
        except:
            self._labels = {}
    
    def _load_dlg(self):
        p = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
        if p:
            with open(p) as f:
                cfg = json.load(f)
            self.ip.set(cfg.get('ip', self.ip.get()))
            self.port.set(cfg.get('port', self.port.get()))
            for k, v in cfg.get('labels', {}).items():
                if int(k) in self.inputs:
                    self.inputs[int(k)].set_label(v)


def main():
    root = tk.Tk()
    try:
        if sys.platform == 'win32':
            from ctypes import windll, byref, c_int, sizeof
            root.update()
            hwnd = windll.user32.GetParent(root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), sizeof(c_int))
    except:
        pass
    
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
