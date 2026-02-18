"""
Integration tests for EasyTrans SDK.

These tests make real HTTP requests to the EasyTrans API using the
official demo/test environment. They are skipped automatically unless
the required environment variables are set.

Required environment variables:
    EASYTRANS_SERVER    - Server URL, e.g. "mytrans.nl"
    EASYTRANS_ENV       - Environment name, e.g. "demo"
    EASYTRANS_USERNAME  - API username
    EASYTRANS_PASSWORD  - API password

All tests use mode="test" so no real orders or customers are ever created.

Running integration tests:
    pytest tests/integration/ -m integration -v
"""
