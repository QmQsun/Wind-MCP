"""
Mock Wind session and data objects for testing without Wind Terminal.

Provides:
- MockWindData: Simulates WindPy result objects
- MockWindAPI: Simulates the w object (w.wss, w.wsd, etc.)
- MockWindSession: Drop-in replacement for WindSession
"""

from datetime import datetime
from typing import Any


class MockWindData:
    """Simulates a WindPy result object."""

    def __init__(
        self,
        error_code: int = 0,
        data: list | None = None,
        fields: list[str] | None = None,
        codes: list[str] | None = None,
        times: list[datetime] | None = None,
    ):
        self.ErrorCode = error_code
        self.Data = data or []
        self.Fields = fields or []
        self.Codes = codes or []
        self.Times = times or []


class MockWindAPI:
    """
    Simulates the WindPy `w` object.

    Register responses with `mock_response(method, args_pattern, response)`.
    Default behavior returns empty MockWindData for unregistered calls.
    """

    def __init__(self):
        self._responses: dict[str, MockWindData] = {}
        self._call_log: list[dict] = []
        self._connected = True
        self._error_injection: dict[str, int] = {}

    def mock_response(self, method: str, response: MockWindData) -> None:
        """Register a mock response for a method."""
        self._responses[method] = response

    def inject_error(self, method: str, error_code: int) -> None:
        """Make a method return an error on next call."""
        self._error_injection[method] = error_code

    def _record_call(self, method: str, *args, **kwargs) -> None:
        self._call_log.append({"method": method, "args": args, "kwargs": kwargs})

    def _get_response(self, method: str, *args, **kwargs) -> MockWindData:
        self._record_call(method, *args, **kwargs)

        # Check error injection first
        if method in self._error_injection:
            code = self._error_injection.pop(method)
            return MockWindData(error_code=code, data=[["Error"]])

        if method in self._responses:
            return self._responses[method]

        # Default: empty success
        return MockWindData()

    def start(self) -> MockWindData:
        self._connected = True
        return MockWindData(error_code=0)

    def stop(self) -> None:
        self._connected = False

    def isconnected(self) -> bool:
        return self._connected

    def wss(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wss", *args, **kwargs)

    def wsd(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wsd", *args, **kwargs)

    def wsi(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wsi", *args, **kwargs)

    def wst(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wst", *args, **kwargs)

    def wsq(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wsq", *args, **kwargs)

    def wset(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wset", *args, **kwargs)

    def edb(self, *args, **kwargs) -> MockWindData:
        return self._get_response("edb", *args, **kwargs)

    def wses(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wses", *args, **kwargs)

    def wsee(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wsee", *args, **kwargs)

    def weqs(self, *args, **kwargs) -> MockWindData:
        return self._get_response("weqs", *args, **kwargs)

    def tdays(self, *args, **kwargs) -> MockWindData:
        return self._get_response("tdays", *args, **kwargs)

    def tdaysoffset(self, *args, **kwargs) -> MockWindData:
        return self._get_response("tdaysoffset", *args, **kwargs)

    def tdayscount(self, *args, **kwargs) -> MockWindData:
        return self._get_response("tdayscount", *args, **kwargs)

    def wpf(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wpf", *args, **kwargs)

    def wps(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wps", *args, **kwargs)

    def wpd(self, *args, **kwargs) -> MockWindData:
        return self._get_response("wpd", *args, **kwargs)


# Pre-built fixtures

def make_wss_fixture(
    codes: list[str], fields: list[str], values: list[list]
) -> MockWindData:
    """
    Build a WSS-style MockWindData.

    values is column-major: values[field_idx][code_idx].
    """
    return MockWindData(
        error_code=0, data=values, fields=fields, codes=codes
    )


def make_wsd_fixture(
    codes: list[str], fields: list[str],
    times: list[datetime], values: list[list]
) -> MockWindData:
    """Build a WSD-style MockWindData."""
    return MockWindData(
        error_code=0, data=values, fields=fields, codes=codes, times=times
    )


def make_wset_fixture(fields: list[str], values: list[list]) -> MockWindData:
    """Build a WSET-style MockWindData (no Codes/Times)."""
    return MockWindData(error_code=0, data=values, fields=fields)
