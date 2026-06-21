import os
import unittest
CURR_DIR = os.path.dirname(__file__)

def get_top_level_directory(start: str = CURR_DIR, indicator: str = "pypps.py", maxiter: int = 10) -> str:
    path = os.path.normpath(start)
    while maxiter > 0:
        if indicator in os.listdir(path):
            return path
        else:
            path = os.path.normpath(path + "/../")
            maxiter -= 1
    raise FileNotFoundError("Can not find the top level directory")
            
def get_test_suite() -> unittest.TestSuite:
    top_level_dir = get_top_level_directory()
    return unittest.TestLoader().discover(CURR_DIR, "test_*.py", top_level_dir)

if __name__ == "__main__":
    test_suite = get_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)