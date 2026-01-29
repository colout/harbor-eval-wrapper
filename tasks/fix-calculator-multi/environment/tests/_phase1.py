import sys
sys.path.insert(0, "/workspace")

from calculator import multiply

assert multiply(10, 5) == 50
assert multiply(-2, 3) == -6
assert multiply(0, 100) == 0

print("phase1: ok")
