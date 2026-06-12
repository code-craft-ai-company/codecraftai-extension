==========================
Code Craft AI Extension
==========================

The ``codecraftai-extension`` package provides the lightweight extension and factory machinery that other ccai packages use to allow third-party code to plug in new resource types, coordinators, and protocol handlers without modifying the host package. Extensions are discovered by scanning the ``ccai.factories`` namespace on ``sys.path`` (and via explicit module registration through ``SuperFactory.add_factory_module``), and are picked up by extension-aware packages such as ``codecraftai-landscaping``, ``codecraftai-interop``, and the ``codecraftai-interop-ext-*`` packages.

Highlights
==========

- ``FactoryExtension`` plus ``FactoryProtocolBase`` and ``SuperFactory`` for pluggable object construction.
- ``ResourceExtension`` for resources that must be discovered and registered at runtime.
- ``ccai.factories`` namespace scanning (plus explicit module registration) so third-party packages can contribute without modifying host code.
- Used as the substrate for the composable ``codecraftai-interop-ext-*`` ecosystem of device types, protocols, and services.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/tests/`` - ``unittest``-based tests.
- ``specs/`` - Requirements, design, and task documentation.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

Activate the virtual environment:

.. code-block:: bash

   source .venv/bin/activate

Run ``unittest`` tests:

.. code-block:: bash

   python -m unittest discover -s source/tests -p "test_*.py"

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Design documentation: ``specs/design.md``
- Requirements: ``specs/requirements.md``
