"""Setup wizard: detect OS, check binaries, install missing dependencies."""
import platform, shutil, subprocess

REQUIRED_BINARIES = [
    ("samtools", "samtools --version"),
    ("bwa-mem2", "bwa-mem2 version"),
    ("gatk", "gatk --version"),
    ("blastn", "blastn -version"),
    ("fastqc", "fastqc --version"),
]

BREW_PACKAGES = {
    "samtools": "samtools", "bwa-mem2": "bwa-mem2",
    "gatk": "brewsci/bio/gatk", "blastn": "blast", "fastqc": "fastqc",
}


def check_binary(name):
    path = shutil.which(name)
    if not path:
        return (name, False, None)
    try:
        result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip().split("\n")[0] if result.returncode == 0 else None
        return (name, True, version)
    except Exception:
        return (name, True, None)


def detect_os():
    system = platform.system()
    if system == "Darwin": return "macos"
    elif system == "Linux": return "linux"
    return "unknown"


def install_via_brew(package):
    try:
        result = subprocess.run(["brew", "install", package], capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception:
        return False
