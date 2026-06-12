"""
.. module:: utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains utility functions used to scan for factory protocol modules
               and factory types.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import importlib
import importlib.util
import os
import sys


from types import ModuleType


is_python3 = sys.version_info[0] == 3
is_python_pre_3_5 = (is_python3 and sys.version_info[1] < 5)


def get_directory_for_code_container(container: ModuleType) -> str:
    """
        Returns the directory associated with a code container (module or package).

        :param container: The module or package object you want to get a directory for.

        :returns: The package directory for a package, or the directory containing the
                  module file for a module.
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


def import_file(name: str, loc: str, by_file_only: bool=False) -> ModuleType:
    """
        Import a module from a specific file path.

        :param name: Name assigned to the loaded module.
        :param loc: Filesystem path to the module file.
        :param by_file_only: Only attempt loading from ``loc`` if ``True``.

        :returns: The imported module.
        :raises: ImportError if the module cannot be loaded by name or from ``loc``.
    """
    mod = None
    if name in sys.modules:
        mod = sys.modules[name]

    if mod is None:
        by_name_error = None

        if not by_file_only:
            # First try to import the module by name only.  If that fails, keep
            # the error so we can surface it as context if the file load also
            # fails (rather than silently discarding it).
            try:
                mod = importlib.import_module(name)
            except ImportError as imp_err:
                by_name_error = imp_err

        if mod is None:
            spec = importlib.util.spec_from_file_location(name, str(loc))
            if spec is None or spec.loader is None:
                errmsg_lines = [
                    f"Unable to import module name='{name}' from location='{loc}'.",
                    "No import spec/loader could be created for the given location (the path may not exist or may not be a valid Python module)."
                ]
                if by_name_error is not None:
                    errmsg_lines.append(f"BY-NAME IMPORT ERROR: {by_name_error}")
                errmsg = os.linesep.join(errmsg_lines)
                raise ImportError(errmsg) from by_name_error

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[name] = mod

    return mod
