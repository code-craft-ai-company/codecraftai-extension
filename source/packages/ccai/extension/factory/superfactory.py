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
from typing import Callable, Generator, List, Type, Union

from ccai.extension.utilities import import_by_name

from ccai.extension.factory.factoryextension import FactoryExtension
from ccai.extension.factory.factoryprotocolbase import FactoryProtocolBase


logger = logging.getLogger()


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
            wmsg = f"Found factory protocol module={fe_module} without an `FactoryExtension` derived class."
            logger.warning(wmsg)

    return factory_types


def scan_ccai_factories_namespace() -> List[str]:

    search_paths = set([p for p in sys.path])

    rel_amr_factories =  os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    search_paths.add(rel_amr_factories)

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

        for fname in filenames:
            if fname.endswith(".py"):
                fcomp = fname[:-3]
                mod_parts_comp = ""
                if len(leafpath_parts) > 0:
                    mod_parts_comp = "." + ".".join(leafpath_parts)

                mod_name = f"{module_prefix}{mod_parts_comp}.{fcomp}"
                modules_found.append(mod_name)

    return modules_found


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
            Create an instance using the first factory that supports the protocol.

            :param factory_method: A callable that is a method of the protocol type that we are going to use
                                   in order to find an extension factory that implements the protocol.
            :param args: Positional arguments to pass to the factory method.
            :param kwargs: Keyword arguments to pass to the factory method.

            :returns: An instance of an object type created by the first factory that supports
                      the protocol factory method provided.
        """

        instance = None

        proto_type_name = factory_method.__qualname__.split('.')[0]
        proto_type: FactoryProtocolBase = factory_method.__globals__[proto_type_name]
        proto_name = proto_type.factory_protocol_name
        factory_method = factory_method.__name__

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

        proto_type_name = factory_method.__qualname__.split('.')[0]
        proto_type: FactoryProtocolBase = factory_method.__globals__[proto_type_name]
        proto_name = proto_type.factory_protocol_name
        factory_method = factory_method.__name__

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
            Return the override type from the first factory that supplies it.
        """

        found_type = None

        get_type_with = None

        proto_type_name = get_type_method.__qualname__.split('.')[0]
        proto_type: FactoryProtocolBase = get_type_method.__globals__[proto_type_name]
        proto_name = proto_type.factory_protocol_name
        get_type_method = get_type_method.__name__

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

        proto_type_name = get_type_method.__qualname__.split('.')[0]
        proto_type: FactoryProtocolBase = get_type_method.__globals__[proto_type_name]
        proto_name = proto_type.factory_protocol_name
        get_type_method = get_type_method.__name__
        
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

