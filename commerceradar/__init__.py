"""CommerceRadar — standard Radar interface over Flomers Commerce KG.

This package provides the standard Radar collector/analyzer/reporter/storage
surface, wrapping the underlying `flomers_kg` knowledge-graph engine. The KG
implementation in `src/flomers_kg/` is preserved unchanged; this package adds
the standard contract expected by radar-dashboard, radar-analysis, radar-ontology.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
