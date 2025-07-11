import logging
import os
import sys
import tempfile
import types
import unittest

from unittest.mock import patch

from automojo.extension.utilities import import_by_name
from automojo.extension.factory.factoryextension import FactoryExtension
from automojo.extension.factory.factoryprotocolbase import FactoryProtocolBase
from automojo.extension.factory.superfactory import (
    is_subclass_of_factory_extension,
    load_and_set_factoryextension_types,
    scan_automojo_factories_namespace,
    scan_for_descendant_modules,
    SuperFactory
)



class ExampleProtocol(FactoryProtocolBase):

    ext_protocol_name = "example"

    def create_thing(self, value):
        raise NotImplementedError()

    def get_type(self):
        raise NotImplementedError()

    def get_many_types(self):
        raise NotImplementedError()


def make_factory(module_name: str, precedence: int, prefix: str):

    protocol_name: str = f"{prefix.lower()}-protocol"

    module = types.ModuleType(module_name)
    code = f"""
from automojo.extension.factory.factoryextension import FactoryExtension
class {prefix}Factory(FactoryExtension):
    PRECEDENCE = {precedence}
    ext_protocol_name = '{protocol_name}'
    @staticmethod
    def create_thing(value):
        return '{prefix}:' + str(value)
    @staticmethod
    def get_type():
        return '{prefix}Type'
    @staticmethod
    def get_many_types():
        return ['{prefix}1', '{prefix}2']
"""
    exec(code, module.__dict__)
    sys.modules[module_name] = module
    return getattr(module, f"{prefix}Factory")



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

    def test_is_subclass_of_factory_extension(self):
        class Child(FactoryExtension):
            pass

        self.assertTrue(is_subclass_of_factory_extension(Child))
        self.assertFalse(is_subclass_of_factory_extension(FactoryExtension))
        self.assertFalse(is_subclass_of_factory_extension(int))

    def test_load_and_set_extension_factory_type_single(self):
        with tempfile.TemporaryDirectory() as td:
            self._write_module(
                td,
                "singlemod",
                "from automojo.extension.factory.factoryextension import FactoryExtension\n"
                "class AF(FactoryExtension):\n    pass\n",
            )
            sys.path.insert(0, td)
            try:
                cls = load_and_set_factoryextension_types("singlemod")
                self.assertIsNotNone(cls)
                self.assertEqual(cls.__name__, "AF")
            finally:
                sys.path.pop(0)
                sys.modules.pop("singlemod", None)

    def test_load_and_set_extension_factory_type_multiple(self):
        with tempfile.TemporaryDirectory() as td:
            self._write_module(
                td,
                "multimod",
                "from automojo.extension.factory.factoryextension import FactoryExtension\n"
                "class AFactory(FactoryExtension):\n    pass\n"
                "class BFactory(FactoryExtension):\n    pass\n",
            )
            sys.path.insert(0, td)
            try:
                logger = logging.getLogger()
                with self.assertLogs(logger, level="WARNING") as cm:
                    cls = load_and_set_factoryextension_types("multimod")
                self.assertIn("Only one ExtensionPoints class is allowed", cm.output[0])
                self.assertEqual(cls.__name__, "AFactory")
            finally:
                sys.path.pop(0)
                sys.modules.pop("multimod", None)

    def test_load_and_set_extension_factory_type_none(self):
        with tempfile.TemporaryDirectory() as td:
            self._write_module(
                td,
                "emptymod",
                "value = 1\n",
            )
            sys.path.insert(0, td)
            try:
                logger = logging.getLogger()
                with self.assertLogs(logger, level="WARNING") as cm:
                    cls = load_and_set_factoryextension_types("emptymod")
                self.assertIn("without an `ExtensionPoints` derived class", cm.output[0])
                self.assertIsNone(cls)
            finally:
                sys.path.pop(0)
                sys.modules.pop("emptymod", None)

    def test_scan_automojo_factories_namespace_discovers(self):
        with tempfile.TemporaryDirectory() as td:
            factories_dir = os.path.join(td, "automojo", "factories")
            os.makedirs(factories_dir)
            self._write_module(factories_dir, "example", "value = 5\n")
            sys.path.insert(0, td)
            try:
                modules = scan_automojo_factories_namespace()
                self.assertIn("automojo.factories.example", modules)
            finally:
                sys.path.pop(0)
                sys.modules.pop("automojo.factories.example", None)

    def test_scan_for_descendant_modules_builds_names(self):
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "sub"))
            self._write_module(td, "a", "")
            self._write_module(os.path.join(td, "sub"), "b", "")
            mods = scan_for_descendant_modules(td, module_prefix="myprefix")
            self.assertIn("myprefix.a", mods)
            self.assertIn("myprefix.sub.b", mods)

    def _write_module(self, directory, name, contents):
        modfile = os.path.join(directory, f"{name}.py")
        with open(modfile, "w") as f:
            f.write(contents)
        return modfile


class TestSuperFactory(unittest.TestCase):
    """
        SuperFactory tests.
    """
    


if __name__ == "__main__":
    unittest.main()
