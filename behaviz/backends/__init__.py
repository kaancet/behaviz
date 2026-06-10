import behaviz.backends.matplotlib
import behaviz.backends.seaborn
import behaviz.backends.bokeh  # noqa: F401

# Validate that every registered plot type is fully implemented across all
# backends and overriders. This runs once at import and raises immediately if
# anything is missing, so errors surface during development rather than at
# call time.
from behaviz.core.registry_validation import validate_registry

validate_registry()
