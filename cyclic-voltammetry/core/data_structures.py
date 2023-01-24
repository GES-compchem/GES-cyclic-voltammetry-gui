from dataclasses import dataclass
from echemsuite.cyclicvoltammetry.read_input import CyclicVoltammetry


@dataclass
class CVExperiment:
    data: CyclicVoltammetry
    area: float
    vref: float
    filename: str


@dataclass
class Trace:
    name: str
    voltage: list
    current: list
    color: str
    linestyle: str
    original_experiment: str
    original_number: int


@dataclass
class PlotSettings:
    normalize_by_area: bool = False
    shift_with_vref: bool = False
    show_markers: bool = False
    set_user_defined_scale: bool = False
    vmin: float = -2.0
    vmax: float = 2.0
    imin: float = -1.0
    imax: float = 1.0