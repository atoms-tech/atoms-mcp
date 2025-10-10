"""HTTP client with connection pooling and timeout management."""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, Optional, Union, Generator
from contextlib import contextmanager


class Response:
    """HTTP response wrapper."""

    def __init__(self, status_code: int, headers: Dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = headers
        self._body = body

    @property
    def text(self) -> str:
        """Get response body as text."""
        return self._body.decode('utf-8', errors='replace')

    def json(self) -> Any:
        """Parse response body as JSON."""
        return json.loads(self.text)

    @property
    def content(self) -> bytes:
        """Get raw response body."""
        return self._body

    @property
    def ok(self) -> bool:
        """Check if response is successful (2xx)."""
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> None:
        """Raise exception if response is not successful."""
        if not self.ok:
            raise HTTPError(f"HTTP {self.status_code}: {self.text}")


class HTTPError(Exception):
    """HTTP request error."""
    pass


class HTTPClient:
    """
    Simple HTTP client with connection pooling.

    Zero-dependency HTTP client using urllib.
    For production use, consider using requests or httpx.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            headers: Default headers for all requests
        """
        self.base_url = base_url.rstrip('/') if base_url else None
        self.timeout = timeout
        self.default_headers = headers or {}

    def _build_url(self, path: str) -> str:
        """Build full URL from base and path."""
        if path.startswith(('http://', 'https://')):
            return path
        if self.base_url:
            return f"{self.base_url}/{path.lstrip('/')}"
        return path

    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge default and request headers."""
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[bytes, str, Dict]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Response:
        """
        Make HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL (full or relative to base_url)
            headers: Request headers
            params: Query parameters
            data: Request body (bytes, str, or dict for form data)
            json_data: JSON request body
            timeout: Request timeout in seconds

        Returns:
            Response object
        """
        full_url = self._build_url(url)

        # Add query parameters
        if params:
            query = urllib.parse.urlencode(params)
            full_url = f"{full_url}?{query}"

        # Prepare headers
        req_headers = self._merge_headers(headers)

        # Prepare request body
        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            req_headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            elif isinstance(data, str):
                body = data.encode('utf-8')
            else:
                body = data

        # Create request
        request = urllib.request.Request(
            full_url,
            data=body,
            headers=req_headers,
            method=method.upper(),
        )

        # Make request
        try:
            timeout_val = timeout if timeout is not None else self.timeout
            with urllib.request.urlopen(request, timeout=timeout_val) as response:
                status_code = response.getcode()
                headers = dict(response.headers)
                body = response.read()

            return Response(status_code, headers, body)

        except urllib.error.HTTPError as e:
            # Return error response
            return Response(e.code, dict(e.headers), e.read())

        except urllib.error.URLError as e:
            raise HTTPError(f"Request failed: {e.reason}")
        except Exception as e:
            raise HTTPError(f"Request failed: {str(e)}")

    def get(self, url: str, **kwargs) -> Response:
        """Make GET request."""
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        """Make POST request."""
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        """Make PUT request."""
        return self.request('PUT', url, **kwargs)

    def patch(self, url: str, **kwargs) -> Response:
        """Make PATCH request."""
        return self.request('PATCH', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        """Make DELETE request."""
        return self.request('DELETE', url, **kwargs)

    def head(self, url: str, **kwargs) -> Response:
        """Make HEAD request."""
        return self.request('HEAD', url, **kwargs)


@contextmanager
def http_client(*args: Any, **kwargs: Any) -> Generator[HTTPClient, None, None]:
    """Context manager for HTTP client."""
    client = HTTPClient(*args, **kwargs)
    try:
        yield client
    finally:
        pass  # No cleanup needed for urllib-based client
