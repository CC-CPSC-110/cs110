import subprocess
import sys

def install(package: str, *args) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, *args])

install("git+https://github.com/CC-CPSC-110/cs110.git#egg=cs110", "--force")