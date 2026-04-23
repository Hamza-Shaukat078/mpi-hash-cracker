from mpi4py import MPI
import hashlib
import itertools
import string
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math

# —— Hash cracking worker —— #
def crack_hash(target_hash, hash_name, char_set, max_length, rank, size, comm):
    total_first = len(char_set)
    chunk = math.ceil(total_first / size)
    start, end = rank * chunk, min((rank + 1) * chunk, total_first)
    sub_first = char_set[start:end]

    for length in range(1, max_length + 1):
        combos = len(sub_first) * (len(char_set) ** (length - 1))
        report_every = max(1, combos // 100)
        tried = 0

        for first in sub_first:
            for suffix in itertools.product(char_set, repeat=length - 1):
                pwd = first + ''.join(suffix)
                tried += 1

                if tried % report_every == 0:
                    comm.send((rank, int(tried / combos * 100)), dest=0, tag=1)

                h = hashlib.new(hash_name, pwd.encode()).hexdigest()
                if h == target_hash:
                    comm.send((rank, 100), dest=0, tag=1)
                    return pwd

        comm.send((rank, 100), dest=0, tag=1)

    return None


# —— Dictionary Attack Worker —— #
def crack_hash_dictionary(target_hash, hash_name, wordlist, rank, size, comm):
    total_words = len(wordlist)
    chunk = math.ceil(total_words / size)
    start, end = rank * chunk, min((rank + 1) * chunk, total_words)
    words = wordlist[start:end]

    report_every = max(1, len(words) // 100)
    tried = 0

    for i, pwd in enumerate(words):
        tried += 1
        if tried % report_every == 0:
            comm.send((rank, int(i / len(words) * 100)), dest=0, tag=1)

        try:
            h = hashlib.new(hash_name, pwd.strip().encode()).hexdigest()
            if h == target_hash:
                comm.send((rank, 100), dest=0, tag=1)
                return pwd.strip()
        except Exception as e:
            continue  # skip invalid hashes

    comm.send((rank, 100), dest=0, tag=1)
    return None


# —— Orchestrator —— #
def run_cracker(cfg, comm, rank, size, gui=None, bars=None, tree=None, status_var=None):
    cfg = comm.bcast(cfg, root=0)
    hashes = cfg['hashes']
    hash_type = cfg['hash_type']

    if cfg['mode'] == 'Brute-force':
        charset = list(cfg['charset'])
        max_len = cfg['max_length']
    elif cfg['mode'] == 'Dictionary':
        wordlist = cfg['wordlist']
    else:
        raise ValueError("Unknown mode")

    for h in hashes:
        if rank == 0:
            status_var.set(f"Cracking {hash_type.upper()} {h[:8]}...")
            for pb in bars.values():
                pb['value'] = 0

        if cfg['mode'] == 'Brute-force':
            pwd = crack_hash(h, hash_type, charset, max_len, rank, size, comm)
        elif cfg['mode'] == 'Dictionary':
            pwd = crack_hash_dictionary(h, hash_type, wordlist, rank, size, comm)

        results = comm.gather(pwd, root=0)

        if rank == 0:
            found = next((p for p in results if p), 'Not found')
            tree.insert('', 'end', values=(h, found))

    if rank == 0:
        status_var.set("All done.")
        messagebox.showinfo("Finished", "All hashes processed.")
        gui.quit()


# —— Main with modern flat GUI styling —— #
def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        root = tk.Tk()
        root.title("Modern MPI Hash Cracker")
        root.geometry("650x600")
        root.configure(bg="#2e2e2e")

        # Style setup
        style = ttk.Style(root)
        style.theme_use('clam')

        PRIMARY_BG = "#2e2e2e"
        SECONDARY_BG = "#3c3f41"
        ACCENT = "#00d8ff"
        FG_TEXT = "#e0e0e0"
        BTN_BG = "#44475a"
        ENTRY_BG = "#3c3f41"
        FONT = ("Segoe UI", 10)

        style.configure("TLabel", background=PRIMARY_BG, foreground=FG_TEXT, font=FONT)
        style.configure("Accent.TLabel", background=PRIMARY_BG, foreground=ACCENT, font=("Segoe UI", 11, "bold"))
        style.configure("TButton", background=BTN_BG, foreground=FG_TEXT, font=FONT, relief="flat", padding=6)
        style.map("TButton", background=[('active', SECONDARY_BG)])
        style.configure("TEntry", fieldbackground=ENTRY_BG, foreground=FG_TEXT, font=FONT)
        style.configure("TCombobox", fieldbackground=ENTRY_BG, foreground=FG_TEXT, background=PRIMARY_BG, font=FONT)
        style.configure("TProgressbar", troughcolor=SECONDARY_BG, background=ACCENT)
        style.configure("TLabelframe", background=PRIMARY_BG, borderwidth=0)
        style.configure("TLabelframe.Label", background=PRIMARY_BG, foreground=ACCENT, font=("Segoe UI", 11, "bold"))

        ttk.Label(root, text="MPI Hash Cracker", style="Accent.TLabel").pack(pady=(15, 5))

        # Load hashes
        top_frame = ttk.Frame(root, style="TLabelframe")
        top_frame.pack(fill='x', padx=20, pady=10)
        hashes = []
        ttk.Button(top_frame, text="📁 Load Hash File", command=lambda: load_file()).pack(side='left')
        file_label = ttk.Label(top_frame, text="No file loaded")
        file_label.pack(side='left', padx=10)

        def load_file():
            path = filedialog.askopenfilename(filetypes=[('Text Files','*.txt')])
            if not path: return
            with open(path) as f:
                hashes.clear()
                hashes.extend(line.strip() for line in f if line.strip())
            file_label.config(text=f"Loaded {len(hashes)} hashes")

        # Mode selector
        mode_frame = ttk.Frame(root, style="TLabelframe")
        mode_frame.pack(fill='x', padx=20, pady=5)
        ttk.Label(mode_frame, text="Attack Mode:").grid(row=0, column=0, sticky='e', pady=5)
        mode_var = tk.StringVar(value='Brute-force')
        ttk.Combobox(mode_frame, textvariable=mode_var,
                     values=['Brute-force', 'Dictionary'], state='readonly', width=15).grid(row=0, column=1, sticky='w', padx=5)

        # Settings grid
        settings = ttk.Frame(root, style="TLabelframe")
        settings.pack(fill='x', padx=20)
        ttk.Label(settings, text="Charset:").grid(row=0, column=0, sticky='e', pady=5)
        charset_entry = ttk.Entry(settings, width=30)
        charset_entry.insert(0, string.ascii_lowercase)
        charset_entry.grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(settings, text="Hash Type:").grid(row=1, column=0, sticky='e', pady=5)
        hash_var = tk.StringVar(value='md5')
        ttk.Combobox(settings, textvariable=hash_var,
                     values=['md5','sha1','sha256'], state='readonly', width=28).grid(row=1, column=1, sticky='w', padx=5)

        ttk.Label(settings, text="Max Length:").grid(row=2, column=0, sticky='e', pady=5)
        maxlen_entry = ttk.Entry(settings, width=5)
        maxlen_entry.insert(0, '5')
        maxlen_entry.grid(row=2, column=1, sticky='w', padx=5)

        # Dictionary file loader
        dict_frame = ttk.Frame(root, style="TLabelframe")
        dict_frame.pack(fill='x', padx=20, pady=5)
        dict_path = ['rockyou.txt']  # mutable to store path
        dict_label = ttk.Label(dict_frame, text=f"Dict: {dict_path[0]}")
        dict_label.pack(side='left', padx=5)

        def load_dict():
            path = filedialog.askopenfilename(filetypes=[('Text Files','*.txt')])
            if path:
                dict_path[0] = path
                dict_label.config(text=f"Dict: {path}")

        ttk.Button(dict_frame, text="📄 Load Dictionary", command=load_dict).pack(side='left')

        # Progress bars
        bars_frame = ttk.Labelframe(root, text="Progress", style="TLabelframe")
        bars_frame.pack(fill='x', padx=20, pady=15)
        bars = {}
        for i in range(size):
            ttk.Label(bars_frame, text=f"Proc {i}").grid(row=i, column=0, padx=5, pady=3)
            bars[i] = ttk.Progressbar(bars_frame, length=400, maximum=100, style="TProgressbar")
            bars[i].grid(row=i, column=1, padx=5, pady=3)

        # Results
        tree = ttk.Treeview(root, columns=('Hash','Password'), show='headings', height=6)
        tree.heading('Hash', text='Hash')
        tree.heading('Password', text='Password')
        tree.tag_configure('odd', background=SECONDARY_BG)
        tree.tag_configure('even', background=PRIMARY_BG)
        tree.pack(fill='both', expand=True, padx=20, pady=10)

        # Status and Start
        bottom = ttk.Frame(root, style="TLabelframe")
        bottom.pack(fill='x', padx=20, pady=10)
        status = tk.StringVar(value='Idle')
        ttk.Label(bottom, textvariable=status).pack(side='left')
        ttk.Button(bottom, text="▶ START", command=lambda: start_crack()).pack(side='right')

        def start_crack():
            if not hashes:
                return messagebox.showwarning("No Data", "Load a hash file first.")

            mode = mode_var.get()
            hash_type = hash_var.get()
            try:
                ml = int(maxlen_entry.get())
                assert ml > 0
            except:
                return messagebox.showerror("Error", "Max Length must be a positive integer.")

            cfg = {
                'hashes': hashes.copy(),
                'hash_type': hash_type,
                'mode': mode
            }

            if mode == 'Brute-force':
                cfg.update({
                    'charset': charset_entry.get(),
                    'max_length': ml
                })
            elif mode == 'Dictionary':
                try:
                    with open(dict_path[0], 'r', encoding='utf-8', errors='ignore') as f:
                        wordlist = [line.rstrip('\n') for line in f]
                    cfg['wordlist'] = wordlist
                except Exception as e:
                    messagebox.showerror("Error", f"Could not read dictionary file:\n{e}")
                    return

            threading.Thread(target=run_cracker,
                             args=(cfg, comm, rank, size, root, bars, tree, status),
                             daemon=True).start()

        # Progress Listener
        def listener():
            while True:
                if comm.Iprobe(source=MPI.ANY_SOURCE, tag=1):
                    r, pct = comm.recv(source=MPI.ANY_SOURCE, tag=1)
                    bars[r]['value'] = pct
                root.update_idletasks()

        threading.Thread(target=listener, daemon=True).start()

        root.mainloop()

    else:
        run_cracker(None, comm, rank, size)

if __name__ == '__main__':
    main()