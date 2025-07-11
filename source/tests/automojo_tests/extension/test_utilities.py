import os
import sys
import tempfile
import types
import unittest


from automojo.extension.utilities import (
    import_by_name,
    import_file,
    get_directory_for_code_container,
)

class TestSuperFactoryHelperFunctions(unittest.TestCase):

    def test_import_by_name_returns_existing(self):
        dummy = types.ModuleType("dummy_mod")
        sys.modules["dummy_mod"] = dummy
        try:
            result = import_by_name("dummy_mod")
            self.assertIs(result, dummy)
        finally:
            del sys.modules["dummy_mod"]

    def test_import_by_name_imports_new_module(self):
        with tempfile.TemporaryDirectory() as td:
            modfile = os.path.join(td, "dmodule.py")
            with open(modfile, "w") as f:
                f.write("value = 42\n")
            sys.path.insert(0, td)
            try:
                result = import_by_name("dmodule")
                self.assertEqual(result.value, 42)
            finally:
                sys.path.pop(0)
                sys.modules.pop("dmodule", None)

    def test_import_file_returns_existing(self):
        dummy = types.ModuleType("dummy_file_mod")
        dummy.flag = True
        sys.modules["dummy_file_mod"] = dummy
        try:
            result = import_file("dummy_file_mod", "unused")
            self.assertIs(result, dummy)
        finally:
            del sys.modules["dummy_file_mod"]

    def test_import_file_loads_from_file(self):
        with tempfile.TemporaryDirectory() as td:
            modfile = os.path.join(td, "afile.py")
            with open(modfile, "w") as mf:
                mf.write("value = 99\n")
            result = import_file("afile", modfile, by_file_only=True)
            try:
                self.assertEqual(result.value, 99)
            finally:
                sys.modules.pop("afile", None)

    def test_get_directory_for_code_container_package(self):
        with tempfile.TemporaryDirectory() as td:
            pkgdir = os.path.join(td, "apkg")
            os.makedirs(pkgdir)
            with open(os.path.join(pkgdir, "__init__.py"), "w"):
                pass
            sys.path.insert(0, td)
            try:
                import importlib
                pkg = importlib.import_module("apkg")
                result = get_directory_for_code_container(pkg)
                self.assertEqual(result, pkgdir)
            finally:
                sys.path.pop(0)
                sys.modules.pop("apkg", None)

    def test_get_directory_for_code_container_module(self):
        with tempfile.TemporaryDirectory() as td:
            modfile = os.path.join(td, "modx.py")
            with open(modfile, "w"):
                pass
            sys.path.insert(0, td)
            try:
                import importlib
                mod = importlib.import_module("modx")
                result = get_directory_for_code_container(mod)
                self.assertEqual(result, td)
            finally:
                sys.path.pop(0)
                sys.modules.pop("modx", None)
