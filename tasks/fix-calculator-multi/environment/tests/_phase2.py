import sys
sys.path.insert(0, "/workspace")

from calculator import power

assert power(2, 3) == 8
assert power(5, 0) == 1
assert power(3, 2) == 9

print("phase2: ok")
