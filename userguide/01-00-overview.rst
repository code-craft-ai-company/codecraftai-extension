.. _01-00-overview:

********
Overview
********

The ``codecraftai-extension`` package provides the extension and factory machinery
that lets other ``codecraftai-*`` packages plug in new resource types,
coordinators, and protocol handlers without modifying the host package. It is a
dependency-light foundation package (standard library only).

It provides two collaborating mechanisms:

Factory extension chain (``ccai.extension.factory``)
====================================================

- ``FactoryProtocolBase`` — base for a *protocol*: a named contract
  (``factory_protocol_name``) plus one or more classmethods that produce objects
  or types.
- ``FactoryExtension`` — base for a *factory*: a class that implements a protocol's
  methods and declares a ``PRECEDENCE``.
- ``SuperFactory`` — maintains the chain of discovered factories, sorted by
  ascending ``PRECEDENCE``. Dispatch helpers locate the factory that implements a
  requested protocol method:

  - ``create_instance_by_order`` — the **highest-precedence** matching factory wins
    (returns ``None`` if none match).
  - ``create_instance_for_each`` — every matching factory contributes an instance.
  - ``get_override_types_by_order`` / ``iterate_override_types_for_each`` — the type
    variants.

Discovery is by scanning the ``ccai.factories`` namespace on ``sys.path`` (see
``scan_ccai_factories_namespace``) plus explicit registration via
``SuperFactory.add_factory_module``. There is no ``entry_points`` mechanism.

Resource extension collectors (``ccai.extension.resource``)
==========================================================

- ``ResourceExtension`` — base type for resources discovered and registered at
  runtime.
- ``collect_resource_extensions_under_folder(extension_folder, ext_base_type, module_base)``
  — walks a folder and returns the direct subclasses of ``ext_base_type`` it finds,
  registering the discovered modules under ``module_base`` (default
  ``ccai.ext.generated``).

See :ref:`02-00-getting-started` for a worked example.
