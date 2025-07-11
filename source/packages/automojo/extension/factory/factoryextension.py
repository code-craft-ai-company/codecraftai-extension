"""
.. module:: factoryextension
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains the FactoryExtension base type.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


class FactoryExtension:
    """
        The :class:`FactoryExtension` serves as the base class for factory extensions or objects that implement
        a specific factory protocol oriented towards the creation of instances of specific objects.  Factory extension
        classes inherit from this type in order to be identified as a participant in the factory extension discovery
        process.
    """

    PRECEDENCE = 0

