import subprocess
import sys

def install(package: str, *args) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, *args])

install("git+https://github.com/CC-CPSC-110/cs110.git", "--force")
install("pygame==2.6.0")
install("dataclasses")
install("requests")
install("typing_extensions")

# subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
