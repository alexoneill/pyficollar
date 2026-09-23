"""HTTP Transport and session management for TryFi."""

from __future__ import annotations
import http.cookiejar
from http.cookiejar import Cookie
import json
import os
from pathlib import Path
from typing import Any, Callable
import urllib.error
import urllib.request

from .const import (
    API_BASE_URL,
    DEFAULT_HEADERS,
    GRAPHQL_ENDPOINT,
)
from .exceptions import FiAuthError, FiError, FiGraphQLError, FiNetworkError


class FiTransport:
    """Manages HTTP communication, cookies, session persistence, and GraphQL operations."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        api_key: str | None = None,
        custom_opener: urllib.request.OpenerDirector | None = None,
        request_interceptor: Callable[[urllib.request.Request], urllib.request.Request] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = custom_opener or urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.request_interceptor = request_interceptor

        self.session_id: str | None = None
        self.user_id: str | None = None
        self.email: str | None = None

        self.base_headers = dict(DEFAULT_HEADERS)
        if api_key:
            self.base_headers["X-Api-Key"] = api_key

    @property
    def is_authenticated(self) -> bool:
        """Return True if session_id is set or fi.sid cookie exists."""
        if self.session_id:
            return True
        for cookie in self.cookie_jar:
            if cookie.name in ("fi.sid", "fi_session_id"):
                return True
        return False

    def set_session(
        self,
        session_id: str,
        user_id: str | None = None,
        email: str | None = None,
        domain: str = "api.tryfi.com",
    ) -> None:
        """Store session identifiers and register session cookies."""
        self.session_id = session_id
        if user_id:
            self.user_id = user_id
        if email:
            self.email = email

        # Ensure cookie jar has fi.sid and fi_session_id cookies
        for name in ("fi.sid", "fi_session_id"):
            c = Cookie(
                version=0,
                name=name,
                value=session_id,
                port=None,
                port_specified=False,
                domain=domain,
                domain_specified=True,
                domain_initial_dot=False,
                path="/",
                path_specified=True,
                secure=True,
                expires=None,
                discard=False,
                comment=None,
                comment_url=None,
                rest={"HttpOnly": None},
                rfc2109=False,
            )
            self.cookie_jar.set_cookie(c)

    def save_session(self, filepath: str | Path) -> None:
        """Serialize current session and cookies to a JSON file."""
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        cookies_data = []
        for c in self.cookie_jar:
            cookies_data.append(
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                    "secure": c.secure,
                    "expires": c.expires,
                }
            )

        payload = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "email": self.email,
            "cookies": cookies_data,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load_session(self, filepath: str | Path) -> bool:
        """Load session and cookies from a saved JSON file."""
        path = Path(filepath).expanduser().resolve()
        if not path.is_file():
            return False

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.session_id = payload.get("session_id")
        self.user_id = payload.get("user_id")
        self.email = payload.get("email")

        # Clear and restore cookies
        self.cookie_jar.clear()
        for c_dict in payload.get("cookies", []):
            cookie = Cookie(
                version=0,
                name=c_dict.get("name", ""),
                value=c_dict.get("value", ""),
                port=None,
                port_specified=False,
                domain=c_dict.get("domain", "api.tryfi.com"),
                domain_specified=True,
                domain_initial_dot=False,
                path=c_dict.get("path", "/"),
                path_specified=True,
                secure=bool(c_dict.get("secure", True)),
                expires=c_dict.get("expires"),
                discard=False,
                comment=None,
                comment_url=None,
                rest={"HttpOnly": None},
                rfc2109=False,
            )
            self.cookie_jar.set_cookie(cookie)

        return self.is_authenticated

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Perform an HTTP request and return JSON decoded response."""
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        req_headers = dict(self.base_headers)
        if headers:
            req_headers.update(headers)

        body_bytes: bytes | None = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        if self.request_interceptor:
            req = self.request_interceptor(req)

        try:
            with self.opener.open(req) as response:
                resp_bytes = response.read()
                if not resp_bytes:
                    return {}
                return json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            resp_body = ""
            try:
                resp_body = e.read().decode("utf-8")
                err_json = json.loads(resp_body)
            except Exception:
                err_json = {}

            if e.code == 401:
                msg = err_json.get("error", {}).get("message") or "Unauthorized: invalid or expired credentials"
                raise FiAuthError(msg) from e
            elif e.code == 403:
                msg = err_json.get("error", {}).get("message") or f"Forbidden: HTTP 403 on {endpoint}"
                raise FiAuthError(msg) from e
            else:
                msg = f"HTTP Error {e.code} for {endpoint}: {resp_body or e.reason}"
                raise FiNetworkError(msg) from e
        except urllib.error.URLError as e:
            raise FiNetworkError(f"Network error connecting to {url}: {e.reason}") from e
        except json.JSONDecodeError as e:
            raise FiNetworkError(f"Invalid JSON returned from {endpoint}: {e}") from e

    def execute_graphql(
        self,
        query: str,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
        op_type: str | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query or mutation against TryFi's GraphQL endpoint."""
        payload: dict[str, Any] = {
            "query": query,
            "variables": variables or {},
        }
        if operation_name:
            payload["operationName"] = operation_name

        headers: dict[str, str] = {}
        if operation_name:
            headers["X-APOLLO-OPERATION-NAME"] = operation_name
        if op_type:
            headers["X-APOLLO-OPERATION-TYPE"] = op_type
        else:
            headers["X-APOLLO-OPERATION-TYPE"] = "mutation" if query.strip().startswith("mutation") else "query"

        result = self.request("POST", GRAPHQL_ENDPOINT, data=payload, headers=headers)

        if "errors" in result and result["errors"]:
            errors = result["errors"]
            first_msg = errors[0].get("message", "Unknown GraphQL error")
            raise FiGraphQLError(f"GraphQL error in {operation_name or 'operation'}: {first_msg}", errors=errors)

        return result
