from .interface import Interface
from .operators import sqrt, cos, sin, tan

import platform
import subprocess
assert platform.system() == "Darwin", "[MetalGPU] MetalGPU is only supported on macOS"
