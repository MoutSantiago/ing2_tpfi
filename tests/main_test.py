import pytest
from main import sumar, restar

# Tests simples
def test_sumar():
  assert sumar(2, 3) == 5

def test_restar():
  assert restar(3, 2) == 1

# Ejecutar muchos tests
@pytest.mark.parametrize("a, b, esperado", [
  (1, 1, 2),
  (0, 0, 0),
  (-1, 1, 0),
  (2.5, 0.5, 3.0),
])
def test_sumar_varios(a, b, esperado):
  assert sumar(a, b) == esperado

# Preparar datos o recursos reutilizables
@pytest.fixture
def usuario():
    return {"nombre": "Ana", "edad": 30}
