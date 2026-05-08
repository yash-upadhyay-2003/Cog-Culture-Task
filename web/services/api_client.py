import httpx
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT", "120"))


class TruthLayerClient:
    """HTTP client for the TruthLayer FastAPI backend."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def verify_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        POST /verify — upload PDF and return verification results.

        Returns:
            Parsed JSON response dict

        Raises:
            ConnectionError: If the API server is unreachable
            ValueError: If the server returns a non-2xx response
            TimeoutError: If the request times out
        """
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                response = client.post(
                    f"{self.base_url}/verify",
                    files={"file": (filename, file_bytes, "application/pdf")}
                )
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to the API at {self.base_url}. "
                "Make sure the backend server is running."
            )
        except httpx.TimeoutException:
            raise TimeoutError(
                f"Request timed out after {TIMEOUT_SECONDS}s. "
                "The document may be too large or the AI service is slow."
            )
        except Exception as e:
            raise RuntimeError(f"Unexpected error contacting API: {e}")

        if response.status_code == 200:
            return response.json()

        # Parse structured error from our API
        try:
            body = response.json()
            # Our structured error format: {success, error, details}
            if "error" in body:
                msg = body["error"]
                details = body.get("details", "")
                raise ValueError(f"{msg} {details}".strip())
            # FastAPI default validation error format
            detail = body.get("detail", response.text)
            raise ValueError(f"API error {response.status_code}: {detail}")
        except ValueError:
            raise
        except Exception:
            raise ValueError(f"API error {response.status_code}: {response.text}")

    def health_check(self) -> bool:
        """Check if the API server is reachable."""
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except Exception:
            return False
