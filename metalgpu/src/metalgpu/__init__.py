from .interface import Interface
from .operators import sqrt, cos, sin, tan

import platform
import subprocess
assert platform.system() == "Darwin", "[MetalGPU] MetalGPU is only supported on macOS"

result = subprocess.run(['uname', '-m'], capture_output=True, text=True, check=True)
architecture = result.stdout.strip()

print(architecture)
