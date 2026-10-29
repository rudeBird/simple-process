# ProcessLens

A native desktop process monitor built with CustomTkinter. It provides searchable process selection, direct PID lookup, live CPU and resident memory charts, spike detection, and detailed process information.

## Run

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` before installing and running.

## Monitor a process

- Type part of a process name or PID into the left search field.
- Select a result, or enter a PID in the header and choose **Open PID**.
- Choose **Start monitoring** to sample once per second. Pause and resume as needed.
- Choose **Finish session** to stop sampling and open the detailed report view with average and peak CPU/memory usage and detected spikes. Return to the dashboard with **Back to process**; the report stays available until you select another process.
- The chart retains the latest 300 samples for the selected process.
- CPU spikes are flagged at 80% or higher; memory jumps are flagged when resident memory rises by at least 20% between samples.
- Use the **Dark mode** switch in the header to change the app appearance.

CPU usage is reported by psutil and can exceed 100% for multithreaded processes. Some process fields are restricted by the operating system; run with suitable permissions to inspect them.

## Build a Windows executable

Install PyInstaller in the virtual environment, then run:

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name ProcessLens --collect-data customtkinter app.py
```

The distributable is written to `dist/ProcessLens/`. Build on the target operating system; Windows, macOS, and Linux executables are platform-specific.
