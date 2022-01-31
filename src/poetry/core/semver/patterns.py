import re


MODIFIERS = (
    "[._-]?"
    r"((?!post)(?:beta|b|c|pre|RC|alpha|a|patch|pl|p|dev)(?:(?:[.-]?\d+)*)?)?"
    r"([+-]?([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?"
)

_COMPLETE_VERSION = (
    rf"v?(?:\d+!)?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?{MODIFIERS}(?:\+[^\s]+)?"
)

COMPLETE_VERSION = re.compile("(?i)" + _COMPLETE_VERSION)

CARET_CONSTRAINT = re.compile(rf"(?i)^\^({_COMPLETE_VERSION})$")
TILDE_CONSTRAINT = re.compile(rf"(?i)^~(?!=)\s*({_COMPLETE_VERSION})$")
TILDE_PEP440_CONSTRAINT = re.compile(rf"(?i)^~=\s*({_COMPLETE_VERSION})$")
X_CONSTRAINT = re.compile(r"^(!=|==)?\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.[xX*])+$")
BASIC_CONSTRAINT = re.compile(rf"(?i)^(<>|!=|>=?|<=?|==?)?\s*({_COMPLETE_VERSION}|dev)")
