"""
Digital Lab Notebook (DLN)
A headless Python library for transparent, searchable, and traceable scientific experiment logging.
"""
__version__ = "0.1.0"

from .dln import DigitalLabNotebook
from .exceptions import ExperimentNotStartedError, ExperimentAlreadyStartedError, ExperimentFinalizedError
from .talos_tools import get_human_narrative_trail

__all__ = [
    "DigitalLabNotebook",
    "ExperimentNotStartedError",
    "ExperimentAlreadyStartedError",
    "ExperimentFinalizedError",
]