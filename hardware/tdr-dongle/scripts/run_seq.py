import subprocess, sys
PY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
T = r"C:\path\to\ND2\tdr-dongle\tools" + "\\"
for s in sys.argv[1:]:
    print("=== ", s, flush=True)
    r = subprocess.run([PY] + [T + s.split()[0]] + s.split()[1:], capture_output=True, text=True)
    print(r.stdout[-8000:], r.stderr[-2000:], flush=True)
print("DONE", flush=True)
