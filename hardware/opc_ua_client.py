"""
hardware/opc_ua_client.py
OPC-UA client wrapper for plant historian / MES integration.
Supports asyncua library with stub fallback.
"""

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from asyncua.sync import Client as _OPCUAClientLib
    _HAS_ASYNCUA = True
except ImportError:
    _HAS_ASYNCUA = False
    logger.info("asyncua not installed — OPCUAClient running in stub mode.")


class OPCUAClient:
    """
    OPC-UA client for integration with:
      - Plant historian (e.g., Kepware, Ignition OPC-UA server)
      - DCS / energy management system
      - Remote monitoring dashboard

    Default endpoint: opc.tcp://localhost:4840/DikiliGeothermal/
    """

    def __init__(self, endpoint: str = "opc.tcp://localhost:4840/DikiliGeothermal/"):
        self.endpoint = endpoint
        self._client  = None
        self._stub_nodes: dict[str, Any] = {}

    def connect(self) -> bool:
        if _HAS_ASYNCUA:
            try:
                self._client = _OPCUAClientLib(self.endpoint)
                self._client.connect()
                logger.info("OPC-UA connected to %s", self.endpoint)
                return True
            except Exception as exc:
                logger.error("OPC-UA connection failed: %s", exc)
                return False
        logger.info("OPC-UA STUB connected to %s", self.endpoint)
        return True

    def disconnect(self):
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
        logger.info("OPC-UA disconnected.")

    def read_node(self, node_id: str) -> Optional[Any]:
        if _HAS_ASYNCUA and self._client:
            try:
                node = self._client.get_node(node_id)
                return node.read_value()
            except Exception as exc:
                logger.error("OPC-UA read error [%s]: %s", node_id, exc)
            return None
        return self._stub_nodes.get(node_id)

    def write_node(self, node_id: str, value: Any) -> bool:
        if _HAS_ASYNCUA and self._client:
            try:
                from asyncua import ua
                node = self._client.get_node(node_id)
                node.write_value(ua.DataValue(ua.Variant(value)))
                return True
            except Exception as exc:
                logger.error("OPC-UA write error [%s]: %s", node_id, exc)
            return False
        self._stub_nodes[node_id] = value
        return True

    def publish_snapshot(self, snapshot: dict) -> int:
        """Write an entire tag snapshot to the OPC-UA server. Returns number written."""
        written = 0
        for tag_id, data in snapshot.items():
            node_id = f"ns=2;s={tag_id}"
            if self.write_node(node_id, data.get("value")):
                written += 1
        logger.debug("OPC-UA published %d nodes.", written)
        return written
