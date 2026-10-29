#!/usr/bin/env python3
"""Curva de los ventiladores de la caja (bricohams-fan)."""
import importlib.util, os

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('fan', os.path.join(AQUI, '..', 'files', 'bin', 'bricohams-fan.py'))
fan = importlib.util.module_from_spec(spec); spec.loader.exec_module(fan)

cfg = {'cpu_min': 55, 'cpu_max': 75, 'caja_min': 35, 'caja_max': 45, 'duty_min': 30, 'hist': 3}
assert fan.curva(45, 28, cfg) == 0                     # todo frío: parados
assert fan.curva(80, 28, cfg) == 100                   # CPU muy caliente
assert fan.curva(45, 50, cfg) == 100                   # caja muy caliente
assert fan.curva(65, 30, cfg) == 65                    # mitad de rampa de CPU: 30 + 0,5·70
assert fan.curva(None, None, cfg) == 100               # sin sensores: a tope
assert fan.curva(53, 30, cfg, ciclo_anterior=40) == 30 # histéresis: sigue al mínimo
assert fan.curva(50, 30, cfg, ciclo_anterior=40) == 0  # por debajo de la histéresis: para
assert fan.rpm(700, 10) == 2100                        # 2 pulsos por vuelta
print('OK test_fan: curva con histéresis, arranque al mínimo y rpm')
