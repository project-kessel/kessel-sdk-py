# Kessel SDK for Python

A Python gRPC library for connecting to [Project Kessel](https://github.com/project-kessel) services. This provides the foundational gRPC client library for Kessel Inventory API, with plans for a higher-level SDK with fluent APIs, OAuth support, and advanced features in future releases.

## Installation

Install the package using pip:

```bash
pip install kessel-sdk
```

## Usage

This library provides direct access to Kessel Inventory API gRPC services. All generated classes are available under the `kessel.inventory` module.

### Basic Example - Check Permissions

```python
import grpc
from kessel.inventory.v1beta2 import (
    inventory_service_pb2_grpc,
    check_request_pb2,
    resource_reference_pb2,
    reporter_reference_pb2,
    subject_reference_pb2,
)

# Create gRPC client (insecure for development)
stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(
    grpc.insecure_channel("localhost:9000")
)

# Create subject reference
subject = subject_reference_pb2.SubjectReference(
    resource=resource_reference_pb2.ResourceReference(
        reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
        resource_id="alice",
        resource_type="principal"
    )
)

# Create resource reference
resource_ref = resource_reference_pb2.ResourceReference(
    resource_id="alice_club",
    resource_type="group",
    reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
)

# Check permissions
try:
    response = stub.Check(
        check_request_pb2.CheckRequest(
            subject=subject,
            relation="member",
            object=resource_ref,
        )
    )
    print(f"Permission check result: {response.allowed}")
except grpc.RpcError as e:
    print(f"Error: {e.details()}")
```

### Report Resource Example

```python
import grpc
from google.protobuf import struct_pb2
from kessel.inventory.v1beta2 import (
    inventory_service_pb2_grpc,
    report_resource_request_pb2,
    resource_representations_pb2,
    representation_metadata_pb2,
)

stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(
    grpc.insecure_channel("localhost:9000")
)

# Build protobuf Struct for common metadata
common_struct = struct_pb2.Struct()
common_struct.update({"workspace_id": "6eb10953-4ec9-4feb-838f-ba43a60880bf"})

# Build protobuf Struct for reporter-specific data  
reporter_struct = struct_pb2.Struct()
reporter_struct.update({
    "satellite_id": "ca234d8f-9861-4659-a033-e80460b2801c",
    "sub_manager_id": "e9b7d65f-3f81-4c26-b86c-2db663376eed",
    "insights_inventory_id": "c4b9b5e7-a82a-467a-b382-024a2f18c129",
    "ansible_host": "host-1",
})

# Create metadata for the resource representation
metadata = representation_metadata_pb2.RepresentationMetadata(
    local_resource_id="854589f0-3be7-4cad-8bcd-45e18f33cb81",
    api_href="https://apiHref.com/",
    console_href="https://www.consoleHref.com/",
    reporter_version="0.2.11",
)

# Build the resource representations
representations = resource_representations_pb2.ResourceRepresentations(
    metadata=metadata,
    common=common_struct,
    reporter=reporter_struct
)

# Create the report request
request = report_resource_request_pb2.ReportResourceRequest(
    type="host",
    reporter_type="hbi",
    reporter_instance_id="0a2a430e-1ad9-4304-8e75-cc6fd3b5441a",
    representations=representations,
)

try:
    response = stub.ReportResource(request)
    print("Resource reported successfully")
except grpc.RpcError as e:
    print(f"Error reporting resource: {e.details()}")
```

### Available Services

The library includes the following gRPC services:

- **KesselInventoryService**: Main inventory service
  - `Check(CheckRequest)` - Check permissions
  - `CheckForUpdate(CheckForUpdateRequest)` - Check for resource updates
  - `ReportResource(ReportResourceRequest)` - Report resource state
  - `DeleteResource(DeleteResourceRequest)` - Delete a resource
  - `StreamedListObjects(StreamedListObjectsRequest)` - Stream resource listings

### Generated Classes

All protobuf message classes are generated and available. Key classes include:

- `CheckRequest`, `CheckResponse`
- `ReportResourceRequest`, `ReportResourceResponse`
- `DeleteResourceRequest`, `DeleteResourceResponse`
- `ResourceReference`, `SubjectReference`
- `ResourceRepresentations`, `RepresentationMetadata`

See the `examples/` directory for complete working examples.

## Development

### Prerequisites

- Python 3.11 or higher
- [buf](https://github.com/bufbuild/buf) for protobuf/gRPC code generation

Install buf:
```bash
# On macOS
brew install bufbuild/buf/buf

# On Linux
curl -sSL "https://github.com/bufbuild/buf/releases/latest/download/buf-$(uname -s)-$(uname -m)" -o "/usr/local/bin/buf" && chmod +x "/usr/local/bin/buf"

# Or see https://docs.buf.build/installation for other options
```

### Setup

```bash
# Install development dependencies
pip install "kessel-sdk[dev]"

# Generate gRPC code from Kessel Inventory API
buf generate
```

### Code Generation

This library uses [buf](https://github.com/bufbuild/buf) to generate Python gRPC code from the official Kessel Inventory API protobuf definitions hosted at `buf.build/project-kessel/inventory-api`.

The generation is configured in `buf.gen.yaml`.

To regenerate the code:

```bash
buf generate
```

This will download the latest protobuf definitions and generate fresh Python classes in the `src/` directory.

### Building and Installing Locally

```bash
# Build and install the package locally
pip install -e .
```

### Code Quality

Format and lint **excluding generated gRPC files** (`*_pb2.py` and `*_pb2_grpc.py`):

```bash
# Auto-format source & examples
black --exclude '.*_pb2(_grpc)?\.py' src/ examples/

# Lint source & examples
flake8 --exclude '*_pb2.py,*_pb2_grpc.py' src/ examples/
```

## Examples

The `examples/` directory contains working examples:

- `check.py` - Permission checking
- `report_resource.py` - Reporting resource state
- `delete_resource.py` - Deleting resources
- `check_for_update.py` - Checking for updates
- `streamed_list_objects.py` - Streaming resource lists

Run examples:

```bash
python -m examples.check
```

### Error Handling

The SDK uses standard gRPC status codes:

```python
try:
    resp = stub.Check(request)
except grpc.RpcError as err:
    if err.code() == grpc.StatusCode.PERMISSION_DENIED:
        print("Permission denied")
    elif err.code() == grpc.StatusCode.UNAVAILABLE:
        print("Service unavailable")
    else:
        print(f"Error: {err.details()}")
```

## Roadmap

This is the foundational gRPC library. Future releases will include:

- **High-level SDK**: Fluent client builder API
- **Authentication**: OAuth 2.0 Client Credentials flow
- **Convenience Methods**: Simplified APIs for common operations

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -am 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

