"""
.. module:: extensionfactory
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains the ExtensionFactory base type.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


class FactoryProtocol:
    """
        The :class:`FactoryProtocol` serves as the base class for factory protocols or objects that implement
        a specific protocol oriented towards the creation of instances of specific objects.  Factory protocol classes
        inherit from this type in order to be identified as a participant in the factory discovery process.
    """

    PRECEDENCE = 0

