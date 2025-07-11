"""
.. module:: factoryprotocolbase
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains the FactoryProtocolBase base type.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Protocol

class FactoryProtocolBase(Protocol):
    """
        The :class:`FactoryProtocolBase` serves as the base type for objects that declare a factory protocol that should be followed
        in order to override or replace functionality of a software component.  :class:`FactoryProtocolBase` provides the base functionality
        for all factory protocols to inherit from.  It defines the contract that all factory protocols must adhere to in order to be
        recognized as a specific and unique factory protocol.

        Subclasses must set ``factory_protocol_name`` to provide a unique identifier for any factory that implements a specific
        factory protocol.
    """

    factory_protocol_name = None

    def __init_subclass__(cls, *args, **kwargs):
        """
            Validates that derived classes specify ``factory_protocol_name``.
        """
        if cls.factory_protocol_name is None:
            errmsg = (
                "The 'protocol_name' class level field must be set on derived protocol types."
            )
            raise RuntimeError(errmsg)
        return super().__init_subclass__(*args, **kwargs)
