.. _02-00-getting-started:

***************
Getting Started
***************

Installation
============

``codecraftai-extension`` is consumed by other ``codecraftai-*`` packages as a git
dependency. For local development from a checkout:

.. code-block:: bash

    ./repository-setup/rehome-repository
    ./development/setup-environment

The package has no third-party runtime dependencies, so it imports directly with
the source packages on ``PYTHONPATH``:

.. code-block:: bash

    PYTHONPATH=source/packages python3 -c "import ccai.extension"

Defining a protocol and a factory
==================================

A *protocol* names a contract; a *factory* implements it and declares a
``PRECEDENCE``:

.. code-block:: python

    from ccai.extension.factory.factoryprotocolbase import FactoryProtocolBase
    from ccai.extension.factory.factoryextension import FactoryExtension

    class WidgetProtocol(FactoryProtocolBase):
        factory_protocol_name = "widget"

        @classmethod
        def create_widget(cls, name):
            raise NotImplementedError()

    class DefaultWidgetFactory(FactoryExtension):
        PRECEDENCE = 10
        factory_protocol_name = "widget"

        @classmethod
        def create_widget(cls, name):
            return f"default-widget:{name}"

Dispatching through the SuperFactory
====================================

.. code-block:: python

    from ccai.extension.factory.superfactory import SuperFactory

    # Load factories from explicitly named modules (and/or the ccai.factories
    # namespace discovered on sys.path).
    factory = SuperFactory(["myproject.widgets.factories"])

    # Highest-PRECEDENCE matching factory wins; returns None if none match.
    widget = factory.create_instance_by_order(WidgetProtocol.create_widget, "gadget")

    # Every matching factory contributes an instance.
    all_widgets = factory.create_instance_for_each(WidgetProtocol.create_widget, "gadget")

A higher-``PRECEDENCE`` factory registered for the same ``factory_protocol_name``
transparently overrides a lower-precedence one for ``create_instance_by_order``.

Discovering resource extensions in a folder
===========================================

.. code-block:: python

    from ccai.extension.resource.resourceextension import (
        ResourceExtension,
        collect_resource_extensions_under_folder,
    )

    found = collect_resource_extensions_under_folder(
        extension_folder="/path/to/generated/extensions",
        ext_base_type=ResourceExtension,
        module_base="ccai.ext.generated",
    )
    # `found` is the list of direct ResourceExtension subclasses discovered.
