import time
import sys
import psutil
import os

from hmi.main_window import SCADAGuiApp

if __name__ == '__main__':
    print("Testing SCADAGuiApp load time...")
    t0 = time.perf_counter()
    app = SCADAGuiApp(['W-01'])
    t1 = time.perf_counter()
    print(f'SCADAGuiApp Instantiation Time: {(t1 - t0)*1000:.2f} ms')
    
    process = psutil.Process(os.getpid())
    print(f"Memory Usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
