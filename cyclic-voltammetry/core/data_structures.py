from dataclasses import dataclass
from echemsuite.cyclicvoltammetry.read_input import CyclicVoltammetry


@dataclass
class CVExperiment:
    data: CyclicVoltammetry
    area: float
    vref: float


@dataclass
class Trace:
    name: str
    voltage: list
    current: list
    color: str
    linestyle: str
    original_experiment: str
    original_number: int