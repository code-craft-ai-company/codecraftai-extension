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

    factory_protocol_name = "example"

    def create_thing(self, value):
        raise NotImplementedError()

    def get_type(self):
        raise NotImplementedError()

    def get_many_types(self):
        raise NotImplementedError()


def make_factory(module_name: str, precedence: int, prefix: str):

    protocol_name: str = ExampleProtocol.factory_protocol_name

    module = types.ModuleType(module_name)
    code = f"""
from automojo.extension.factory.factoryextension import FactoryExtension
class {prefix}Factory(FactoryExtension):
    PRECEDENCE = {precedence}
    factory_protocol_name = '{protocol_name}'
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
                classes = load_and_set_factoryextension_types("singlemod")
                self.assertEqual(len(classes), 1)
                self.assertEqual(classes[0].__name__, "AF")
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
                classes = load_and_set_factoryextension_types("multimod")
                self.assertEqual(len(classes), 2)
                names = {cls.__name__ for cls in classes}
                self.assertIn("AFactory", names)
                self.assertIn("BFactory", names)
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
                classes = load_and_set_factoryextension_types("emptymod")
                self.assertEqual(classes, [])
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
    def setUp(self):
        """Create example factory modules for each test."""
        self.mod_a = "moda"
        self.mod_b = "modb"

        make_factory(self.mod_a, 10, "A")
        make_factory(self.mod_b, 5, "B")

        self.modules = [self.mod_a, self.mod_b]
        self.extra_modules = []

    def tearDown(self):
        """Remove any modules created during testing."""
        for mod in self.modules + self.extra_modules:
            sys.modules.pop(mod, None)

    def test_init_loads_sorted_factories(self):
        sf = SuperFactory(self.modules)
        names = [cls.__name__ for cls in sf.extension_factories]
        self.assertEqual(names, ["BFactory", "AFactory"])
        for mod in self.modules:
            self.assertIn(mod, sf.factory_modules)

    def test_add_factory_module(self):
        sf = SuperFactory([self.mod_a])

        mod_c = "modc"
        make_factory(mod_c, 1, "C")
        self.extra_modules.append(mod_c)

        sf.add_factory_module(mod_c)

        names = [cls.__name__ for cls in sf.extension_factories]
        self.assertEqual(names, ["CFactory", "AFactory"])
        self.assertIn(mod_c, sf.factory_modules)

    def test_create_instance_by_order(self):
        sf = SuperFactory(self.modules)
        result = sf.create_instance_by_order(ExampleProtocol.create_thing, "val")
        self.assertEqual(result, "A:val")

    def test_create_instance_for_each(self):
        sf = SuperFactory(self.modules)
        result = sf.create_instance_for_each(ExampleProtocol.create_thing, "one")
        self.assertEqual(result, ["B:one", "A:one"])

    def test_get_override_types_by_order(self):
        sf = SuperFactory(self.modules)
        result = sf.get_override_types_by_order(ExampleProtocol.get_type)
        self.assertEqual(result, "AType")

    def test_iterate_override_types_for_each(self):
        sf = SuperFactory(self.modules)
        result = list(sf.iterate_override_types_for_each(ExampleProtocol.get_many_types))
        self.assertEqual(result, ["B1", "B2", "A1", "A2"])

if __name__ == "__main__":
    unittest.main()
