# MPI Hash Cracker

A high-performance, distributed password hash cracking tool built with **Python** and **MPI (mpi4py)**. Leverages parallel processing to distribute cracking workloads across multiple processes, dramatically reducing crack time compared to single-threaded tools.

---

## Features

- **Two Attack Modes**
  - Brute-force — exhaustively tries all character combinations up to a configurable max length
  - Dictionary — tests passwords from a wordlist (e.g. `rockyou.txt`)
- **Multiple Hash Algorithms** — MD5, SHA-1, SHA-256
- **MPI Parallelism** — work is evenly partitioned across all MPI processes for true parallel execution
- **Modern Dark GUI** — built with Tkinter, featuring per-process progress bars and a live results table
- **Flexible Input** — load any `.txt` hash file or dictionary via file picker

---

## Screenshots

> GUI running with 4 MPI processes cracking MD5 hashes in parallel.

```
┌─────────────────────────────────────────┐
│           MPI Hash Cracker              │
├─────────────────────────────────────────┤
│  [Load Hash File]   Loaded 5 hashes     │
│  Attack Mode:  [Brute-force ▾]          │
│  Charset:      abcdefghijklmnopqrstuvwxyz│
│  Hash Type:    [md5 ▾]                  │
│  Max Length:   5                        │
├─────────────────────────────────────────┤
│  Progress                               │
│  Proc 0  ████████████████░░░░  80%      │
│  Proc 1  ██████████████████░░  90%      │
│  Proc 2  ████████████░░░░░░░░  60%      │
│  Proc 3  ██████████████████░░  90%      │
├─────────────────────────────────────────┤
│  Hash               │ Password          │
│  5f4dcc3b5aa765d... │ password          │
│  e10adc3949ba59a... │ 123456            │
└─────────────────────────────────────────┘
```

---

## Requirements

- Python 3.8+
- [mpi4py](https://mpi4py.readthedocs.io/)
- An MPI implementation (e.g. [Microsoft MPI](https://learn.microsoft.com/en-us/message-passing-interface/microsoft-mpi) on Windows, or OpenMPI on Linux/macOS)
- Tkinter (bundled with standard Python)

Install dependencies:

```bash
pip install mpi4py
```

---

## Usage

Run with a single process (no parallelism):

```bash
python passwordcracker.py
```

Run with N parallel MPI processes:

```bash
mpiexec -n 4 python passwordcracker.py
```

> Replace `4` with the number of CPU cores you want to utilize.

### Steps

1. Click **Load Hash File** and select a `.txt` file containing one hash per line.
2. Select your **Attack Mode**: `Brute-force` or `Dictionary`.
3. Configure **Charset**, **Hash Type**, and **Max Length** (brute-force) or load a **Dictionary** file.
4. Click **START** — results appear in the table as hashes are cracked.

---

## Project Structure

```
mpi-hash-cracker/
├── passwordcracker.py       # Main application (MPI + GUI)
├── sample_hashes.txt        # Sample MD5/SHA hashes for testing
├── 5_letter_hashes.txt      # 5-character password hashes
├── custom_password_hashes.txt
├── md5_wordlist.txt         # Precomputed MD5 wordlist
├── sha1_wordlist.txt        # Precomputed SHA-1 wordlist
├── rockyou.txt              # Classic password dictionary
└── README.md
```

---

## How It Works

```
Rank 0 (Master)          Rank 1..N (Workers)
──────────────────        ──────────────────────
  Broadcast config   →    Receive config
  per-hash loop           per-hash loop
  ↓                         crack assigned chunk
  Gather results     ←    Send found password (or None)
  ↓
  Display in GUI
```

The character set (or wordlist) is evenly divided among all MPI processes. Each process independently tests its share and reports its result back to rank 0, which collects and displays the first non-null result.

---

## Supported Hash Types

| Algorithm | Example Hash |
|-----------|-------------|
| MD5       | `5f4dcc3b5aa765d61d8327deb882cf99` |
| SHA-1     | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| SHA-256   | `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` |

---

## Academic Context

This project was developed as part of the **Parallel and Distributed Computing** course (Semester 6). It demonstrates:

- MPI process communication with `mpi4py`
- Work partitioning and load balancing across processes
- Inter-process messaging (`comm.send`, `comm.recv`, `comm.gather`, `comm.bcast`)
- Combining parallel backend logic with a GUI frontend using threading

---

## Disclaimer

This tool is developed **strictly for educational purposes** as part of a university project. Use it only on hashes you own or have explicit permission to test. Unauthorized use against third-party systems is illegal and unethical.

---

## License

MIT License — feel free to use, modify, and distribute with attribution.
