from importlib.metadata import distribution as _DIST

_DIST_INFO = _DIST(__package__ or __name__)
_DIST_META = dict(_DIST_INFO.metadata)
__version__ = _DIST_META['Version']
__description__ = _DIST_META['Summary']
__build__ = "20240429"
__name__ = _DIST_META['Name']
