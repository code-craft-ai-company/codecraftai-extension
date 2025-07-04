"""
.. module:: utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains utility functions used to scan for factory protocol modules
               and factory types.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import importlib
import importlib.util
import os
import sys
import traceback


from types import ModuleType


is_python3 = sys.version_info[0] == 3
is_python_pre_3_5 = (is_python3 and sys.version_info[1] < 5)


def get_directory_for_code_container(container: str) -> str:
    """
        Returns the directory for a code container (module or package)

        :param container: The code container you want to get a directory for.

        :returns: The string that represents the parent directory of the code
                  container specified.
    """
    if hasattr(container, '__path__'):
        container_dir = str(container.__path__[0]).rstrip(os.sep)
    elif hasattr(container, '__file__'):
        container_dir = os.path.dirname(container.__file__).rstrip(os.sep)
    else:
        raise RuntimeError("Unable to get parent dir for module") from None

    return container_dir


def import_by_name(modulename: str) -> ModuleType:
    """
        Imports a module by name.
    """

    mod = None
    if modulename in sys.modules:
        mod = sys.modules[modulename]
    else:
        mod = importlib.import_module(modulename)

    return mod


def import_file(name: str, loc: str, by_file_only=False) -> ModuleType:
    """
        Import a module from a specific file path.

        :param name: Name assigned to the loaded module.
        :param loc: Filesystem path to the module file.
        :param by_file_only: Only attempt loading from ``loc`` if ``True``.

        :returns: The imported module.
    """
    mod = None
    if name in sys.modules:
        mod = sys.modules[name]

    if mod is None:

        while True:
            if not by_file_only:
                # First try to import the module by name only
                try:
                    mod = importlib.import_module(name)
                    break
                except ImportError:
                    errmsg = traceback.format_exc()
                    pass

            spec = importlib.util.spec_from_file_location(name, str(loc))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[name] = mod
            break

    return mod
