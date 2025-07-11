
import os
import sys
import tempfile
import unittest


from automojo.extension.utilities import import_by_name

class TestSuperFactoryHelperFunctions(unittest.TestCase):

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