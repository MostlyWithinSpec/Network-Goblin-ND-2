# export DSN and launch Freerouting in the background
import pcbnew, subprocess, os, sys
P = r"C:\path\to\ND2\tdr-dongle"
R = P + r"\route"
os.makedirs(R, exist_ok=True)
b = pcbnew.LoadBoard(P + r"\tdr-dongle.kicad_pcb")
print("dsn", pcbnew.ExportSpecctraDSN(b, R + r"\tdr-dongle.dsn"))
java = r"C:\path\to\ND2\_libcache\tools\jre25\jdk-25.0.4.1+1-jre\bin\java.exe"
jar = r"C:\path\to\ND2\_libcache\tools\freerouting-2.4.1.jar"
passes = sys.argv[1] if len(sys.argv) > 1 else "100"
for f in ("tdr-dongle.ses", "fr.log"):
    try: os.remove(os.path.join(R, f))
    except OSError: pass
log = open(R + r"\fr.log", "w")
p = subprocess.Popen([java, "-Xmx4g", "-jar", jar, "-de", R + r"\tdr-dongle.dsn", "-do", R + r"\tdr-dongle.ses",
                      "-mp", passes, "--gui.enabled=false"], stdout=log, stderr=subprocess.STDOUT, cwd=R,
                     creationflags=0x00000008 | 0x00000200)
open(R + r"\fr.pid", "w").write(str(p.pid))
print("started pid", p.pid)
