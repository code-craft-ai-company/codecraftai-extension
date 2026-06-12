"""
.. module:: extensionsuperfactory
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains the `ExtensionSuperFactory` object which is used to
               create a singleton instance for dynamically loading type extensions.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import inspect
import logging
import os
import sys


from operator import attrgetter
from typing import Callable, Generator, List, Tuple, Type, Union

from ccai.extension.utilities import import_by_name

from ccai.extension.factory.factoryextension import FactoryExtension
from ccai.extension.factory.factoryprotocolbase import FactoryProtocolBase


logger = logging.getLogger(__name__)


def is_subclass_of_factory_extension(cand_type):
    """
        Returns a boolean value indicating if the candidate type is a subclass of :class:`FactoryExtension`.
    """
    is_scoep = False
    if inspect.isclass(cand_type):
        if cand_type != FactoryExtension and issubclass(cand_type, FactoryExtension):
            is_scoep = True

    return is_scoep


def load_and_set_factoryextension_types(module_name: str) -> List[FactoryExtension]:
    """
        Scans the module provided for :class:`FactoryExtension` derived classes.
    """
    factory_types = []

    fe_module = import_by_name(module_name)
    class_items = inspect.getmembers(fe_module, is_subclass_of_factory_extension)

    factory_types = []
    for _, cls_type in class_items:
        type_module_name = cls_type.__module__
        if type_module_name == fe_module.__name__:
            factory_types.append(cls_type)
        else:
            # The class is a FactoryExtension subclass that was re-exported
            # (imported) into this module but defined elsewhere.  We register
            # it only under its defining module to avoid duplicate registration,
            # so we skip it here. This is expected, not an error.
            dmsg = f"Skipping factory class '{cls_type.__name__}' re-exported into module={fe_module.__name__}; it is registered under its defining module '{type_module_name}'."
            logger.debug(dmsg)

    return factory_types


def scan_ccai_factories_namespace() -> List[str]:

    search_paths = set([p for p in sys.path])

    # __file__ == .../source/packages/ccai/extension/factory/superfactory.py.
    # Four dirname() calls climb to the packages root (.../source/packages), which
    # is the directory that *contains* the 'ccai' package — the correct base for
    # the 'ccai/factories' join below. (The prior three-call version yielded
    # .../source/packages/ccai and produced a never-existing 'ccai/ccai/factories'.)
    packages_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    search_paths.add(packages_root)

    modules_found = []

    for dir_path in search_paths:
        check_dir = os.path.join(dir_path, "ccai", "factories")
        if os.path.exists(check_dir) and os.path.isdir(check_dir):
            check_dir_modules = scan_for_descendant_modules(check_dir)
            modules_found.extend(check_dir_modules)

    return modules_found


def scan_for_descendant_modules(scan_dir: str, module_prefix: str="ccai.factories") -> List[str]:

    modules_found = []

    for dirpath, dirnames, filenames in os.walk(scan_dir):
        leafpath = dirpath[len(scan_dir):].strip(os.sep)
        leafpath_parts = []
        if len(leafpath) > 0:
            leafpath_parts = leafpath.split(os.sep)

        mod_parts_comp = ""
        if len(leafpath_parts) > 0:
            mod_parts_comp = "." + ".".join(leafpath_parts)

        for fname in filenames:
            if not fname.endswith(".py"):
                continue

            if fname == "__init__.py":
                # Emit the package's own importable name rather than a
                # '<pkg>.__init__' alias.  Importing the alias would re-execute
                # the package as a second, distinct module object, registering
                # any factory classes defined in __init__.py as duplicates.
                mod_name = f"{module_prefix}{mod_parts_comp}"
            else:
                fcomp = fname[:-3]
                mod_name = f"{module_prefix}{mod_parts_comp}.{fcomp}"

            if mod_name not in modules_found:
                modules_found.append(mod_name)

    return modules_found


def resolve_protocol_dispatch(factory_method: Callable) -> Tuple[str, str]:
    """
        Resolves the dispatch keys for a protocol factory method.

        :param factory_method: A method of a protocol type used to locate an
            extension factory that implements that protocol.

        :returns: A tuple of (factory_protocol_name, method_name).
        :raises: RuntimeError when the protocol class cannot be resolved from
            the method's module globals (e.g. a nested or mixin-inherited
            method whose owning protocol is not a top-level module name).
    """
    method_qualname = factory_method.__qualname__
    proto_type_name = method_qualname.split('.')[0]
    method_globals = factory_method.__globals__

    if proto_type_name not in method_globals:
        errmsg_lines = [
            f"SuperFactory could not resolve the protocol class '{proto_type_name}' that defines factory method '{method_qualname}'.",
            "The protocol class must be a top-level name in the module where the method is defined (not nested or mixin-inherited).",
            f"METHOD MODULE: {getattr(factory_method, '__module__', '<unknown>')}"
        ]
        errmsg = os.linesep.join(errmsg_lines)
        raise RuntimeError(errmsg)

    proto_type: FactoryProtocolBase = method_globals[proto_type_name]
    proto_name = proto_type.factory_protocol_name
    method_name = factory_method.__name__

    rtnval = (proto_name, method_name)
    return rtnval


class SuperFactory:
    """
        A :class:`SuperFactory` object is used to maintain a chain of factory types that
        can be traversed in order to locate a factory that implements a specific protocol
        in order to enable various types of overload or overinstance states.
    """

    def __init__(self, factory_modules: List[str]):
        """
            Constructs the super factory and loads factory modules.

            :param factory_modules: Additional factory module paths to load.
        """

        self._factory_modules = scan_ccai_factories_namespace()
        if len(factory_modules) > 0:
            self._factory_modules.extend(factory_modules)

        self._protocol_factories: List[Union[FactoryExtension, FactoryProtocolBase]] = []

        for smod in self._factory_modules:
            factory_types = load_and_set_factoryextension_types(smod)
            for ftype in factory_types:
                self._protocol_factories.append(ftype)

        self._protocol_factories.sort(key=attrgetter('PRECEDENCE'))

        return

    @property
    def extension_factories(self):
        """
            List of loaded extension factory types.
        """
        item_list = [item for item in self._protocol_factories]
        return item_list

    @property
    def factory_modules(self):
        """
            List of module names searched for factories.
        """
        item_list = [item for item in self._factory_modules]
        return item_list

    def add_factory_module(self, factory_module: str):
        """
            Can be used by super factory consumers to app the path of a wellknown factory module.
        """
        if factory_module not in self._factory_modules:
            self._factory_modules.append(factory_module)

            factory_types = load_and_set_factoryextension_types(factory_module)
            for ftype in factory_types:
                self._protocol_factories.append(ftype)
            
            self._protocol_factories.sort(key=attrgetter('PRECEDENCE'))

        return

    def create_instance_by_order(self, factory_method: Callable, *args, **kwargs) -> Union[object, None]:
        """
            Create an instance using the highest-precedence factory that supports the protocol.

            Factories are consulted in ascending PRECEDENCE order and the last (highest
            PRECEDENCE) match wins, so a higher-precedence factory overrides lower ones.

            :param factory_method: A callable that is a method of the protocol type that we are going to use
                                   in order to find an extension factory that implements the protocol.
            :param args: Positional arguments to pass to the factory method.
            :param kwargs: Keyword arguments to pass to the factory method.

            :returns: An instance of an object type created by the highest-precedence factory that
                      supports the protocol factory method provided, or ``None`` if no factory matches.
        """

        instance = None

        proto_name, factory_method = resolve_protocol_dispatch(factory_method)

        create_instance: Callable = None

        for factory_type in self._protocol_factories:
            if hasattr(factory_type, factory_method):
                factory_proto_name = factory_type.factory_protocol_name
                if factory_proto_name == proto_name:
                    create_instance = getattr(factory_type, factory_method)
        
        if create_instance is not None:
            instance = create_instance(*args, **kwargs)

        return instance

    def create_instance_for_each(self, factory_method: Callable, *args, **kwargs) -> List[object]:
        """
            Create an instance using each factory that supports the protocol.
        """

        list_of_instances = []

        proto_name, factory_method = resolve_protocol_dispatch(factory_method)

        for factory_type in self._protocol_factories:
            if hasattr(factory_type, factory_method):
                factory_proto_name = factory_type.factory_protocol_name
                if factory_proto_name == proto_name:
                    create_instance = getattr(factory_type, factory_method)
                    instance = create_instance(*args, **kwargs)
                    list_of_instances.append(instance)

        return list_of_instances

    def get_override_types_by_order(self, get_type_method: Callable) -> Union[Type, List[Type], None]:
        """
            Return the override type from the highest-precedence factory that supplies it.

            Factories are consulted in ascending PRECEDENCE order and the last (highest
            PRECEDENCE) match wins.
        """

        found_type = None

        get_type_with = None

        proto_name, get_type_method = resolve_protocol_dispatch(get_type_method)

        for factory_type in self._protocol_factories:
            if hasattr(factory_type, get_type_method):
                factory_proto_name = factory_type.factory_protocol_name
                if factory_proto_name == proto_name:
                    get_type_with = getattr(factory_type, get_type_method)
        
        if get_type_with is not None:
            found_type = get_type_with()
        
        return found_type
    
    def iterate_override_types_for_each(self, get_type_method: Callable, iterate_type_lists: bool = True) -> Generator[Union[Type, List[Type], None], None, None]:
        """
            Yield override types from each factory in order.
        """

        found_type = None

        get_type_with = None

        proto_name, get_type_method = resolve_protocol_dispatch(get_type_method)

        for factory_type in self._protocol_factories:
            if hasattr(factory_type, get_type_method):
                factory_proto_name = factory_type.factory_protocol_name
                if factory_proto_name == proto_name:
                    get_type_with = getattr(factory_type, get_type_method)

                    found_type = get_type_with()

                    if iterate_type_lists and type(found_type) is list:
                        for ftitem in found_type:
                            yield ftitem
                    else:
                        yield found_type

