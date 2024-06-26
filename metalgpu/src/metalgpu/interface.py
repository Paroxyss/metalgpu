import ctypes
import numpy as np

import os
import platform
import subprocess

from buffer import Buffer

class Interface:
    def __init__(self):
        _objPath = os.path.dirname(__file__)

        result = subprocess.run(['uname', '-m'], capture_output=True, text=True, check=True)
        architecture = result.stdout.strip()
        if architecture == "arm64":
            self._metal = ctypes.cdll.LoadLibrary(_objPath + "/lib/libmetalgpucpp-arm.dylib")
        else:
            # Check that the path isnt empty
            assert os.path.exists(_objPath + "/lib/libmetalgpucpp-x86.dylib"), "[MetalGPU] Could not find the library"
            self._metal = ctypes.cdll.LoadLibrary(_objPath + "/lib/libmetalgpucpp-x86.dylib")

        self._init_functions()
        self._init()
        self._loaded_shader = ""
        self._shader_from_path = False
        self.current_function = ""

    def __del__(self):
        self._deleteInstance()

    def _init_functions(self):
        self._init = self._metal.init
        self._createBuffer = self._metal.createBuffer
        self._createLibrary = self._metal.createLibrary
        self._setFunction = self._metal.setFunction
        self._runFunction = self._metal.runFunction
        self._releaseBuffer = self._metal.releaseBuffer
        self._getBufferPointer = self._metal.getBufferPointer
        self._deleteInstance = self._metal.deleteInstance
        self._createLibraryFromString = self._metal.createLibraryFromString

        self._init.argtypes = []
        self._createBuffer.argtypes = [ctypes.c_int]
        self._createLibrary.argtypes = [ctypes.c_char_p]
        self._setFunction.argtypes = [ctypes.c_char_p]
        self._runFunction.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        self._releaseBuffer.argtypes = [ctypes.c_int]
        self._getBufferPointer.argtypes = [ctypes.c_int]
        self._deleteInstance.argtypes = []
        self._createLibraryFromString.argtypes = [ctypes.c_char_p]

        self._init.restype = None
        self._createBuffer.restype = ctypes.c_int
        self._createLibrary.restype = None
        self._setFunction.restype = None
        self._runFunction.restype = None
        self._releaseBuffer.restype = None
        self._getBufferPointer.restype = ctypes.POINTER(ctypes.c_int)
        self._deleteInstance.restype = None
        self._createLibraryFromString.argtypes = [ctypes.c_char_p]

    def create_buffer(self, bufsize : int, bufTypeString):
        assert bufsize > 0, "[MetalGPU] Buffer size must be greater than 0"
        bufType = Interface.resolveType(bufTypeString)
        number = self._createBuffer(ctypes.sizeof(bufType) * bufsize)
        self._getBufferPointer.restype = ctypes.POINTER(bufType)
        buffPointer = self._getBufferPointer(number)
        buff = Buffer(buffPointer, bufsize, self, number)
        return buff

    def load_shader(self, shaderPath : str):
        self._createLibrary(shaderPath.encode('utf-8'))
        self._loaded_shader = shaderPath
        self._shader_from_path = True

    def set_function(self, functionName : str):
        self._setFunction(functionName.encode('utf-8'))
        self.current_function = functionName

    def run_function(self, numThreads : int, buffers : list):
        bufferList = []
        for buff in buffers:
            if buff is None:
                bufferList.append(-1)
            elif isinstance(buff, Buffer):
                bufferList.append(buff.bufNum)
            else:
                raise Exception("Unsupported buffer type")
        bufferArr = np.array(bufferList).astype(np.int32)
        self._runFunction(numThreads, bufferArr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), len(bufferArr))

    def release_buffer(self, bufnum : int):
        self._releaseBuffer(bufnum)

    def array_to_buffer(self, array):
        if isinstance(array, np.ndarray):
            if array.ndim != 1: raise Exception("[MetalGPU] Array must be 1D")
        else:
            array = np.array(array)
            if array.ndim != 1: raise Exception("[MetalGPU] Array must be 1D")

        type = array.dtype
        if type == np.int32: type = ctypes.c_int
        elif type == np.float32: type = ctypes.c_float
        elif type == np.int16: type = ctypes.c_short
        elif type == np.int8: type = ctypes.c_byte
        elif type == np.uint8: type = ctypes.c_ubyte
        elif type == np.uint16: type = ctypes.c_ushort
        elif type == np.uint32: type = ctypes.c_uint
        elif type == np.uint64: type = ctypes.c_ulonglong

        # Cast to types for the unsupported ones, caused by Metal not by choice here.
        elif type == np.int64:
            type = ctypes.c_int
            array = array.astype(np.int32)
        elif type == np.float64:
            type = ctypes.c_float
            array = array.astype(np.float32)
        else: raise Exception("Unsupported data type")

        buffer = self.create_buffer(len(array), type)

        buffer.contents[:] = array
        return buffer

    def load_shader_from_string(self, libStr : str):
        self._createLibraryFromString(libStr.encode('utf-8'))
        self._loaded_shader = libStr
        self._shader_from_path = False

    def resolveType(type):
        # Takes in a stringed type and returns the corresponding ctypes type
        ctype_types = { 
            ctypes.c_int, ctypes.c_float, ctypes.c_double, ctypes.c_longlong,
            ctypes.c_short, ctypes.c_byte, ctypes.c_ubyte, ctypes.c_ushort,
            ctypes.c_uint, ctypes.c_ulonglong 
        }

        if type in ctype_types:
            return type

        if type == "int": return ctypes.c_int
        elif type == "float": return ctypes.c_float
        elif type == "double": return ctypes.c_double
        elif type == "longlong": return ctypes.c_longlong
        elif type == "short": return ctypes.c_short
        elif type == "byte": return ctypes.c_byte
        elif type == "ubyte": return ctypes.c_ubyte
        elif type == "ushort": return ctypes.c_ushort
        elif type == "uint": return ctypes.c_uint
        elif type == "ulonglong": return ctypes.c_ulonglong
        else: raise Exception("Unsupported data type")

        return ctypes.c_int

