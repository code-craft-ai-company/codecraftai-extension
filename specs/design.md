# Code Craft AI Extension Framework Design Document

## Overview

The Code Craft AI Extension Framework is a sophisticated plugin architecture designed to enable dynamic loading, discovery, and management of extensible components in Python applications. The framework provides a robust foundation for building modular, testable automation tools with pluggable functionality.

## Architecture

### Core Components

The framework consists of three primary subsystems:

1. **Factory Extension System** - Implements the Factory pattern with protocol-based discovery
2. **Resource Extension System** - Provides dynamic resource discovery and collection
3. **Utility Layer** - Common functionality for module loading and introspection

### Package Structure

```
ccai/extension/
├── constants.py           # Framework constants
├── utilities.py          # Core utility functions
├── factory/              # Factory pattern implementation
│   ├── factoryextension.py      # Base factory extension class
│   ├── factoryprotocolbase.py  # Protocol definition base
│   └── superfactory.py         # Factory orchestration engine
└── resource/             # Resource extension system
    └── resourceextension.py     # Resource discovery and collection
```

## Factory Extension System

### Design Principles

The factory system implements a **Protocol-Oriented Factory Pattern** that enables:

- **Dynamic Discovery**: Automatic scanning and loading of factory implementations
- **Precedence-Based Ordering**: Factories are sorted by precedence for predictable behavior
- **Protocol Compliance**: Type-safe factory implementations through protocol definitions
- **Multiple Creation Strategies**: Support for single-instance and multi-instance creation patterns

### Key Components

#### FactoryProtocolBase

Defines the contract that all factory protocols must implement:

```python
class FactoryProtocolBase(Protocol):
    factory_protocol_name = None  # Must be set by subclasses
```

**Responsibilities:**
- Establishes protocol identity through `factory_protocol_name`
- Validates protocol implementation at class definition time
- Provides type safety for factory method resolution

#### FactoryExtension

Base class for all factory implementations:

```python
class FactoryExtension:
    PRECEDENCE = 0  # Lower values = higher priority
```

**Responsibilities:**
- Marks classes as factory participants
- Defines execution precedence for factory resolution
- Provides inheritance hierarchy for factory discovery

#### SuperFactory

The orchestration engine that manages factory lifecycles:

**Core Capabilities:**
- **Automatic Discovery**: Scans `ccai.factories` namespace and additional modules
- **Precedence Management**: Sorts factories by `PRECEDENCE` attribute (ascending order)
- **Protocol Resolution**: Matches factory methods to protocol definitions; iterates all matching factories and uses the last match (lowest precedence wins for `by_order` methods)
- **Multiple Creation Modes**:
  - `create_instance_by_order()`: Iterates all matching factories, returns result from last match
  - `create_instance_for_each()`: Returns list from all matching factories
  - `get_override_types_by_order()`: Iterates all matching factories, returns type from last match
  - `iterate_override_types_for_each()`: Yields types from all factories

### Factory Discovery Algorithm

1. **Namespace Scanning**: Searches all directories in `sys.path` for `ccai/factories`
2. **Module Loading**: Dynamically imports discovered Python modules
3. **Type Inspection**: Identifies classes inheriting from `FactoryExtension`
4. **Protocol Matching**: Associates factories with protocols via `factory_protocol_name`
5. **Precedence Sorting**: Orders factories by `PRECEDENCE` attribute

### Usage Patterns

#### Protocol Definition
```python
class DeviceProtocol(FactoryProtocolBase):
    factory_protocol_name = "device"
    
    def create_device(self, device_type: str) -> Device:
        raise NotImplementedError()
```

#### Factory Implementation
```python
class NetworkDeviceFactory(FactoryExtension):
    PRECEDENCE = 10
    factory_protocol_name = "device"
    
    @staticmethod
    def create_device(device_type: str) -> Device:
        return NetworkDevice(device_type)
```

#### Factory Usage
```python
factory = SuperFactory(["my.custom.factories"])
device = factory.create_instance_by_order(
    DeviceProtocol.create_device, 
    "router"
)
```

## Resource Extension System

### Design Philosophy

The resource system provides **Dynamic Component Discovery** for collecting and managing extension classes across codebases.

### Key Features

- **Hierarchical Scanning**: Recursively discovers extensions in package hierarchies
- **Flexible Loading**: Supports both module-based and file-based loading
- **Type Safety**: Uses inheritance-based filtering for extension identification
- **Key Generation**: Creates unique identifiers for discovered extensions

### Core Functions

#### collect_resource_extensions_under_code_container()

Scans Python packages/modules for extension classes:

**Algorithm:**
1. Traverses package directory structure
2. Imports each Python module
3. Inspects module members for extension classes
4. Filters by direct inheritance from specified base type (only direct subclasses, not transitive)
5. Returns collection of discovered extension name-type pairs as `list[tuple[str, type]]`

#### collect_resource_extensions_under_folder()

Scans filesystem directories for extension classes:

**Returns:** `list[tuple[str, type]]` — name-type pairs from `inspect.getmembers`

**Notes:**
- Skips `__init__.py` files (only processes non-init Python files)
- Uses `import_file` with `by_file_only=True` for loading

#### generate_extension_key()

Creates hierarchical identifiers for extensions:
- Format: `"parent/child/extension"`
- Enables organized extension management
- Supports namespace collision resolution

## Utility Layer

### Module Management

The utilities module provides robust module loading capabilities:

#### import_by_name()
- Imports modules by string name
- Handles module caching via `sys.modules`
- Supports standard Python import resolution

#### import_file()
- Loads modules from specific file paths
- Bypasses standard import mechanisms when needed
- Supports dynamic code loading scenarios

#### get_directory_for_code_container()
- Resolves filesystem paths for modules/packages
- Handles both `__path__` (packages) and `__file__` (modules)
- Enables directory-based operations on code containers

### Cross-Platform Compatibility

The framework supports multiple Python versions and platforms:
- **Python 3.x**: Full compatibility with modern Python versions
- **Legacy Support**: Handles pre-3.5 Python versions
- **Platform Agnostic**: Works across Darwin, Linux, Unix, Windows

## Testing Strategy

### Test Coverage

The framework includes comprehensive unit tests covering:

#### Utility Functions
- Module import mechanisms (by name and by file)
- Directory resolution for code containers
- Error handling for invalid modules

#### Factory System
- Factory discovery and loading
- Protocol matching and resolution
- Precedence-based ordering
- Multiple creation strategies
- SuperFactory lifecycle management

#### Resource System
- Extension discovery in packages
- File-based extension loading
- Key generation algorithms

### Test Patterns

Following the repository's unittest conventions:

```python
class TestFactorySystem(unittest.TestCase):
    
    def setUp(self):
        # Establish test conditions
        
    def tearDown(self):
        # Clean up test artifacts
        
    def test_specific_functionality(self):
        # Test individual components in isolation
```

## Design Patterns

### Factory Pattern
- **Abstract Factory**: `FactoryProtocolBase` defines creation interfaces
- **Concrete Factories**: `FactoryExtension` subclasses implement specific creation logic
- **Factory Registry**: `SuperFactory` manages factory discovery and selection

### Protocol Pattern
- **Type Safety**: Protocol definitions ensure consistent factory interfaces
- **Runtime Validation**: Protocol compliance checked at factory registration
- **Flexible Implementation**: Factories can implement multiple protocols

### Plugin Architecture
- **Dynamic Discovery**: Runtime scanning for extension components
- **Loose Coupling**: Extensions register through inheritance, not explicit registration
- **Extensibility**: New factory types can be added without framework modification

## Performance Considerations

### Lazy Loading
- Modules loaded on-demand during discovery
- Factory instances created only when needed
- Minimal startup overhead

### Caching Strategy
- Module imports cached in `sys.modules`
- Factory collections cached in `SuperFactory` instances
- Directory scanning results cached per factory instance

### Scalability
- Linear complexity for factory discovery (O(n) modules)
- Constant time factory lookup after initial discovery
- Memory usage scales with number of discovered factories

## Security Considerations

### Code Execution
- Dynamic imports limited to specified namespaces
- File-based imports require explicit paths
- No arbitrary code execution from external sources

### Module Isolation
- Factory modules loaded in standard Python import context
- No special privileges or elevated permissions
- Standard Python security model applies

## Extension Points

### Custom Factory Protocols
Developers can create domain-specific factory protocols:

```python
class CustomProtocol(FactoryProtocolBase):
    factory_protocol_name = "custom"
    
    def create_custom_object(self, config):
        raise NotImplementedError()
```

### Additional Factory Modules
SuperFactory supports loading additional factory modules:

```python
factory = SuperFactory([
    "my.project.factories",
    "third.party.extensions"
])
```

### Resource Extension Base Types
Custom resource extension hierarchies:

```python
class MyResourceExtension(ResourceExtension):
    pass

extensions = collect_resource_extensions_under_code_container(
    my_package, 
    MyResourceExtension
)
```

## Future Enhancements

### Potential Improvements

1. **Configuration-Based Discovery**: Support for declarative factory registration
2. **Dependency Injection**: Integration with DI containers for factory dependencies
3. **Async Support**: Asynchronous factory methods and resource loading
4. **Metrics Integration**: Performance monitoring for factory operations
5. **Hot Reloading**: Runtime factory updates without application restart

### Backward Compatibility

The framework maintains strict backward compatibility:
- Public APIs remain stable across versions
- Deprecation warnings for removed functionality
- Migration guides for breaking changes

## Conclusion

The Code Craft AI Extension Framework provides a robust, scalable foundation for building extensible automation tools. Its protocol-oriented design ensures type safety while maintaining flexibility, and its comprehensive testing coverage ensures reliability in production environments.

The framework's modular architecture enables teams to build complex automation systems with clear separation of concerns, pluggable functionality, and maintainable codebases that prioritize debuggability and readability over performance optimization.