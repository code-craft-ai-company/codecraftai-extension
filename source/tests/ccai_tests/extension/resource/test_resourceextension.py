import os
import sys
import unittest
import tempfile

from ccai.extension.resource.resourceextension import (
    ResourceExtension,
    collect_resource_extensions_under_code_container,
    collect_resource_extensions_under_folder,
    generate_extension_key,
)

class TestResourceExtension(unittest.TestCase):

    def test_collect_extensions_and_key(self):
        with tempfile.TemporaryDirectory() as td:
            pkgdir = os.path.join(td, 'pkg')
            os.makedirs(pkgdir)
            with open(os.path.join(pkgdir, '__init__.py'), 'w'):
                pass
            with open(os.path.join(pkgdir, 'ext.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class Child(ResourceExtension):\n    pass\n')
            sys.path.insert(0, td)
            try:
                import importlib
                pkg = importlib.import_module('pkg')
                exts = collect_resource_extensions_under_code_container(pkg, ResourceExtension)
                names = [name for name, _ in exts]
                self.assertIn('Child', names)

                exts2 = collect_resource_extensions_under_folder(pkgdir, ResourceExtension, module_base='pkg')
                names2 = [name for name, _ in exts2]
                self.assertIn('Child', names2)

                key = generate_extension_key('a', 'b', 'c')
                self.assertEqual(key, 'a/b/c')
            finally:
                sys.path.pop(0)

    def test_collect_extensions_nested_package(self):
        with tempfile.TemporaryDirectory() as td:
            pkg_name = 'pkg_nested'
            pkg_root = os.path.join(td, pkg_name)
            sub_pkg = os.path.join(pkg_root, 'sub')
            os.makedirs(sub_pkg)

            with open(os.path.join(pkg_root, '__init__.py'), 'w'):
                pass
            with open(os.path.join(sub_pkg, '__init__.py'), 'w'):
                pass
            with open(os.path.join(pkg_root, 'rootext.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class RootExt(ResourceExtension):\n    pass\n')
            with open(os.path.join(sub_pkg, 'subext.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class SubExt(ResourceExtension):\n    pass\n')

            sys.path.insert(0, td)
            try:
                import importlib
                pkg = importlib.import_module(pkg_name)
                exts = collect_resource_extensions_under_code_container(pkg, ResourceExtension)
                names = {name for name, _ in exts}
                self.assertIn('RootExt', names)
                self.assertIn('SubExt', names)
            finally:
                sys.path.pop(0)
                sys.modules.pop(pkg_name, None)
                sys.modules.pop(f"{pkg_name}.rootext", None)
                sys.modules.pop(f"{pkg_name}.sub.subext", None)

    def test_collect_only_direct_subclasses(self):
        with tempfile.TemporaryDirectory() as td:
            pkg_name = 'pkg_direct'
            pkg_root = os.path.join(td, pkg_name)
            os.makedirs(pkg_root)
            with open(os.path.join(pkg_root, '__init__.py'), 'w'):
                pass
            with open(os.path.join(pkg_root, 'ext.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class Base(ResourceExtension):\n    pass\n'
                        'class Child(Base):\n    pass\n')

            sys.path.insert(0, td)
            try:
                import importlib
                pkg = importlib.import_module(pkg_name)
                exts = collect_resource_extensions_under_code_container(pkg, ResourceExtension)
                names = {name for name, _ in exts}
                self.assertIn('Base', names)
                self.assertNotIn('Child', names)
            finally:
                sys.path.pop(0)
                sys.modules.pop(pkg_name, None)
                sys.modules.pop(f"{pkg_name}.ext", None)

    def test_collect_from_single_module_without_extensions(self):
        with tempfile.TemporaryDirectory() as td:
            pkg_name = 'pkg_single'
            pkg_root = os.path.join(td, pkg_name)
            os.makedirs(pkg_root)
            with open(os.path.join(pkg_root, '__init__.py'), 'w'):
                pass
            with open(os.path.join(pkg_root, 'empty.py'), 'w') as mf:
                mf.write('VALUE = 1\n')

            sys.path.insert(0, td)
            try:
                import importlib
                pkg = importlib.import_module(pkg_name)
                exts = collect_resource_extensions_under_code_container(pkg, ResourceExtension)
                self.assertEqual(exts, [])
            finally:
                sys.path.pop(0)
                sys.modules.pop(pkg_name, None)
                sys.modules.pop(f'{pkg_name}.empty', None)

    def test_collect_extensions_under_nested_folder(self):
        with tempfile.TemporaryDirectory() as td:
            ext_root = os.path.join(td, 'exts')
            os.makedirs(os.path.join(ext_root, 'sub1'))
            os.makedirs(os.path.join(ext_root, 'sub2', 'nested'))

            with open(os.path.join(ext_root, 'sub1', 'aext.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class AExt(ResourceExtension):\n    pass\n')

            with open(os.path.join(ext_root, 'sub2', 'nested', 'bext.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class BExt(ResourceExtension):\n    pass\n')

            exts = collect_resource_extensions_under_folder(ext_root, ResourceExtension, module_base='gen')
            names = {name for name, _ in exts}
            self.assertIn('AExt', names)
            self.assertIn('BExt', names)

    def test_collect_extensions_ignores_non_extension_files(self):
        with tempfile.TemporaryDirectory() as td:
            ext_root = os.path.join(td, 'exts')
            os.makedirs(ext_root)

            with open(os.path.join(ext_root, '__init__.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class ShouldSkip(ResourceExtension):\n    pass\n')

            with open(os.path.join(ext_root, 'good.py'), 'w') as f:
                f.write('from ccai.extension.resource.resourceextension import ResourceExtension\n'
                        'class Good(ResourceExtension):\n    pass\n')

            # Non-python file that should be ignored
            with open(os.path.join(ext_root, 'bad.txt'), 'w') as f:
                f.write('class Bad(ResourceExtension): pass')

            exts = collect_resource_extensions_under_folder(ext_root, ResourceExtension, module_base='gen')
            names = {name for name, _ in exts}
            self.assertIn('Good', names)
            self.assertNotIn('ShouldSkip', names)
            self.assertNotIn('Bad', names)

    def test_generate_extension_key_empty(self):
        self.assertEqual(generate_extension_key(), '')

if __name__ == '__main__':
    unittest.main()
