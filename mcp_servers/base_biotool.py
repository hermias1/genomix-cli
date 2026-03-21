"""Base class for bioinformatics tool MCP servers."""
import json, logging, os, shutil, subprocess

if os.environ.get("GENOMIX_QUIET"):
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)


class BaseBiotoolServer:
    def __init__(self, binary_name, binary_path=None):
        self.binary_name = binary_name
        self.binary_path = binary_path or binary_name

    def check_binary(self):
        return shutil.which(self.binary_path) is not None

    def run_command(self, args, timeout=300):
        cmd = [self.binary_path] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                return json.dumps({"error": f"{self.binary_name} exited with code {result.returncode}", "stderr": result.stderr.strip()})
            return result.stdout
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"{self.binary_name} timed out"})
        except FileNotFoundError:
            return json.dumps({"error": f"{self.binary_name} not found. Run 'genomix setup'."})
