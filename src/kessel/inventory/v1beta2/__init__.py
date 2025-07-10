from collections.abc import Hashable

from kessel.grpc import BaseClientBuilder
from kessel.inventory.v1beta2.inventory_service_pb2_grpc import KesselInventoryServiceStub


class ClientBuilder(BaseClientBuilder):
    """
    A builder for creating a Inventory gRPC client (sync or asyncio variants).

    Constructors "with defaults" provide a convenient way
    to set up the client with common, recommended defaults.
    """

    def build_inventory_stub(self) -> KesselInventoryServiceStub:
        return self.build_stub(KesselInventoryServiceStub)

    def build_or_get_inventory_stub(self, cacheKey: Hashable) -> KesselInventoryServiceStub:
        return self.build_or_get_existing_stub(cacheKey, KesselInventoryServiceStub)
