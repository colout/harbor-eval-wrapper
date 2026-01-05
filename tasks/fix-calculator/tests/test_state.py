import sys
sys.path.insert(0, "/workspace")

from calculator import add, subtract, multiply, divide

def test_add():
    assert add(10, 5) == 15
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(5, 10) == -5
    assert subtract(0, 0) == 0

def test_multiply():
    assert multiply(10, 5) == 50
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0

def test_divide():
    assert divide(10, 5) == 2.0
    assert divide(7, 2) == 3.5
    assert divide(0, 5) == 0.0
