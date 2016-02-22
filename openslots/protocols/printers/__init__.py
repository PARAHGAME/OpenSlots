"""Communication protocols for various printers. This package defines a
class exposing an API which classes for individual protocols inherit
from, as well as a metaclass to make importing the correct printer
according to your platform config easier.

Usage:

from openslots.protocols.printers import Printer

printer = Printer('fl:///dev/tty3')  # or:
printer = Printer('trans://COM3')  # using RS232, or:
printer = Printer('usb://16f5')  # futurelogic, or:
printer = Printer('usb://0613')  # transact, using GDS
"""