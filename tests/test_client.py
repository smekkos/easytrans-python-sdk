"""
Unit tests for EasyTransClient.

Tests all client functionality using mocked HTTP responses (responses library).
No real API calls are made during testing.
"""

import json
import pytest
import responses
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError

from easytrans import EasyTransClient
from easytrans.exceptions import (
    EasyTransAPIError,
    EasyTransAuthError,
    EasyTransOrderError,
    EasyTransDestinationError,
    EasyTransPackageError,
    EasyTransCustomerError,
    EasyTransValidationError,
)


class TestClientInitialization:
    """Test client initialization and configuration."""

    def test_client_initialization(self):
        """Test basic client initialization."""
        client = EasyTransClient(
            server_url="mytrans.nl",
            environment_name="demo",
            username="test_user",
            password="test_pass",
        )

        assert client.base_url == "https://mytrans.nl/demo/import_json.php"
        assert client.username == "test_user"
        assert client.password == "test_pass"
        assert client.default_mode == "test"
        assert client.timeout == 30

    def test_client_custom_settings(self):
        """Test client with custom timeout and mode."""
        client = EasyTransClient(
            server_url="mytrans.be",
            environment_name="production",
            username="user",
            password="pass",
            default_mode="effect",
            timeout=60,
        )

        assert client.base_url == "https://mytrans.be/production/import_json.php"
        assert client.default_mode == "effect"
        assert client.timeout == 60

    def test_client_context_manager(self):
        """Test client can be used as context manager."""
        with EasyTransClient(
            server_url="mytrans.nl",
            environment_name="demo",
            username="user",
            password="pass",
        ) as client:
            assert client is not None
            assert client.session is not None


class TestAuthenticationPayload:
    """Test authentication payload construction."""

    @responses.activate
    def test_authentication_merged_with_orders(self, client, sample_order, success_order_response):
        """Verify authentication is correctly merged with order data in request body."""
        # Mock API response
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=success_order_response,
            status=200,
        )

        # Make request
        client.import_orders([sample_order], mode="effect")

        # Verify request structure
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)

        # Authentication should be a sibling to orders
        assert "authentication" in request_body
        assert "orders" in request_body

        # Verify authentication fields
        auth = request_body["authentication"]
        assert auth["username"] == "test_user"
        assert auth["password"] == "test_pass"
        assert auth["type"] == "order_import"
        assert auth["mode"] == "effect"
        assert auth["version"] == 2

        # Verify orders data is present
        assert len(request_body["orders"]) == 1
        assert request_body["orders"][0]["productno"] == 2

    @responses.activate
    def test_authentication_with_return_rates(self, client, sample_order, success_order_response_with_rates):
        """Test return_rates parameter is included when requested."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=success_order_response_with_rates,
            status=200,
        )

        client.import_orders([sample_order], return_rates=True)

        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["authentication"]["return_rates"] is True

    @responses.activate
    def test_authentication_with_return_documents(self, client, sample_order, success_order_response):
        """Test return_documents parameter is included when specified."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=success_order_response,
            status=200,
        )

        client.import_orders([sample_order], return_documents="label10x15")

        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["authentication"]["return_documents"] == "label10x15"


class TestOrderImport:
    """Test order import functionality."""

    @responses.activate
    def test_successful_order_import(self, client, sample_order, success_order_response):
        """Test successful order import returns OrderResult."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=success_order_response,
            status=200,
        )

        result = client.import_orders([sample_order], mode="effect")

        assert result.mode == "effect"
        assert result.total_orders == 1
        assert result.total_order_destinations == 2
        assert result.total_order_packages == 1
        assert len(result.new_ordernos) == 1
        assert result.new_ordernos[0] == 29145

        # Verify tracking info
        assert "29145" in result.order_tracktrace
        tt = result.order_tracktrace["29145"]
        assert tt.local_trackingnr == "AEZS2MRZGE2DK"
        assert tt.status == "accepted"
        assert "tracktrace.php" in tt.local_tracktrace_url

    @responses.activate
    def test_order_import_with_rates(self, client, sample_order, success_order_response_with_rates):
        """Test order import with rate calculation."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=success_order_response_with_rates,
            status=200,
        )

        result = client.import_orders([sample_order], return_rates=True)

        assert result.order_rates is not None
        assert "29145" in result.order_rates
        
        rates = result.order_rates["29145"]
        assert rates.order_total_excluding_vat == 158.74
        assert rates.order_total_including_vat == 192.08
        assert len(rates.rates) == 2

    @responses.activate
    def test_order_import_test_mode(self, client, sample_order):
        """Test order import in test mode (validation only)."""
        test_response = {
            "result": {
                "mode": "test",
                "total_orders": 1,
                "total_order_destinations": 2,
                "total_order_packages": 1,
                "result_description": "Test import completed successfully. No changes have been made.",
                "new_ordernos": [],
                "order_tracktrace": {},
            }
        }

        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=test_response,
            status=200,
        )

        result = client.import_orders([sample_order], mode="test")

        assert result.mode == "test"
        assert result.total_orders == 1
        assert len(result.new_ordernos) == 0  # No orders created in test mode


class TestCustomerImport:
    """Test customer import functionality."""

    @responses.activate
    def test_successful_customer_import(self, client, sample_customer, success_customer_response):
        """Test successful customer import returns CustomerResult."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=success_customer_response,
            status=200,
        )

        result = client.import_customers([sample_customer], mode="effect")

        assert result.mode == "effect"
        assert result.total_customers == 1
        assert result.total_customer_contacts == 1
        assert len(result.new_customernos) == 1
        assert result.new_customernos[0] == 12345

        # Verify user IDs
        assert 12345 in result.new_userids
        assert result.new_userids[12345] == [201]

    @responses.activate
    def test_customer_import_test_mode(self, client, sample_customer):
        """Test customer import in test mode."""
        test_response = {
            "result": {
                "mode": "test",
                "total_customers": 1,
                "total_customer_contacts": 1,
                "result_description": "Test import completed successfully. No changes have been made.",
                "new_customernos": [],
                "new_userids": {},
            }
        }

        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=test_response,
            status=200,
        )

        result = client.import_customers([sample_customer], mode="test")

        assert result.mode == "test"
        assert len(result.new_customernos) == 0


class TestErrorHandling:
    """Test error handling and exception mapping."""

    @responses.activate
    def test_auth_error_raises_correct_exception(self, client, sample_order, error_auth_response):
        """Verify errorno 12 raises EasyTransAuthError."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=error_auth_response,
            status=200,
        )

        with pytest.raises(EasyTransAuthError) as exc_info:
            client.import_orders([sample_order])

        assert "12" in str(exc_info.value)
        assert "Login attempt failed" in str(exc_info.value)

    @responses.activate
    def test_order_error_raises_correct_exception(self, client, sample_order, error_order_response):
        """Verify errorno 21 raises EasyTransOrderError."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=error_order_response,
            status=200,
        )

        with pytest.raises(EasyTransOrderError) as exc_info:
            client.import_orders([sample_order])

        assert "21" in str(exc_info.value)
        assert "productno" in str(exc_info.value)

    @responses.activate
    def test_destination_error_raises_correct_exception(self, client, sample_order, error_destination_response):
        """Verify errorno 30 raises EasyTransDestinationError."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=error_destination_response,
            status=200,
        )

        with pytest.raises(EasyTransDestinationError) as exc_info:
            client.import_orders([sample_order])

        assert "30" in str(exc_info.value)
        assert "destinations" in str(exc_info.value).lower()

    @responses.activate
    def test_customer_error_raises_correct_exception(self, client, sample_customer, error_customer_response):
        """Verify errorno 50 raises EasyTransCustomerError."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=error_customer_response,
            status=200,
        )

        with pytest.raises(EasyTransCustomerError) as exc_info:
            client.import_customers([sample_customer])

        assert "50" in str(exc_info.value)
        assert "company_name" in str(exc_info.value)

    @responses.activate
    def test_json_parse_error(self, client, sample_order):
        """Test handling of invalid JSON response."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            body="Invalid JSON {{{",
            status=200,
        )

        with pytest.raises(EasyTransAPIError) as exc_info:
            client.import_orders([sample_order])

        assert "Invalid JSON response" in str(exc_info.value)

    @responses.activate
    def test_http_timeout(self, client, sample_order):
        """Test handling of HTTP timeout."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            body=Timeout(),
        )

        with pytest.raises(EasyTransAPIError) as exc_info:
            client.import_orders([sample_order])

        assert "timeout" in str(exc_info.value).lower()

    @responses.activate
    def test_http_500_error(self, client, sample_order):
        """Test handling of HTTP 500 error."""
        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json={"error": "Internal server error"},
            status=500,
        )

        with pytest.raises(EasyTransAPIError) as exc_info:
            client.import_orders([sample_order])

        assert "500" in str(exc_info.value)


class TestWebhookParsing:
    """Test webhook payload parsing."""

    def test_parse_webhook_dict(self, webhook_payload_finished):
        """Test parsing webhook from dictionary."""
        webhook = EasyTransClient.parse_webhook(webhook_payload_finished)

        assert webhook.companyId == 2000
        assert webhook.order.orderNo == 1234
        assert webhook.order.status == "finished"
        assert webhook.order.subStatusName == "Delivered at the neighbours"
        assert webhook.order.externalId == "test-order-12345"
        assert len(webhook.order.destinations) == 2

    def test_parse_webhook_json_string(self, webhook_payload_finished):
        """Test parsing webhook from JSON string."""
        json_str = json.dumps(webhook_payload_finished)
        webhook = EasyTransClient.parse_webhook(json_str)

        assert webhook.companyId == 2000
        assert webhook.order.orderNo == 1234

    def test_parse_webhook_bytes(self, webhook_payload_finished):
        """Test parsing webhook from bytes."""
        json_bytes = json.dumps(webhook_payload_finished).encode("utf-8")
        webhook = EasyTransClient.parse_webhook(json_bytes)

        assert webhook.companyId == 2000
        assert webhook.order.orderNo == 1234

    def test_parse_webhook_with_valid_api_key(self, webhook_payload_finished):
        """Test webhook parsing with API key validation (success)."""
        headers = {"X-API-Key": "b6e6a42d-1243-453d-81ba-0dac775227fc"}
        
        webhook = EasyTransClient.parse_webhook(
            webhook_payload_finished,
            expected_api_key="b6e6a42d-1243-453d-81ba-0dac775227fc",
            headers=headers,
        )

        assert webhook.companyId == 2000

    def test_parse_webhook_with_invalid_api_key(self, webhook_payload_finished):
        """Test webhook parsing with invalid API key raises error."""
        headers = {"X-API-Key": "wrong-api-key"}
        
        with pytest.raises(EasyTransAuthError) as exc_info:
            EasyTransClient.parse_webhook(
                webhook_payload_finished,
                expected_api_key="b6e6a42d-1243-453d-81ba-0dac775227fc",
                headers=headers,
            )

        assert "Invalid webhook API key" in str(exc_info.value)

    def test_parse_webhook_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        with pytest.raises(EasyTransValidationError) as exc_info:
            EasyTransClient.parse_webhook("Invalid JSON {{{")

        assert "Invalid JSON" in str(exc_info.value)

    def test_parse_webhook_missing_fields(self):
        """Test parsing webhook with missing required fields."""
        invalid_payload = {"companyId": 2000}  # Missing eventTime and order

        with pytest.raises(EasyTransValidationError) as exc_info:
            EasyTransClient.parse_webhook(invalid_payload)

        assert "missing required fields" in str(exc_info.value)

    def test_parse_webhook_collected_status(self, webhook_payload_collected):
        """Test parsing webhook with collected status."""
        webhook = EasyTransClient.parse_webhook(webhook_payload_collected)

        assert webhook.order.status == "collected"
        assert len(webhook.order.destinations) == 1
        assert webhook.order.destinations[0].taskType == "pickup"
        assert webhook.order.destinations[0].taskResult.signedBy == "Mr. Johnson"

    def test_webhook_get_event_datetime(self, webhook_payload_finished):
        """Test parsing eventTime to datetime object."""
        webhook = EasyTransClient.parse_webhook(webhook_payload_finished)
        
        dt = webhook.get_event_datetime()
        assert dt.year == 2026
        assert dt.month == 2
        assert dt.day == 18
        assert dt.hour == 14


class TestAllErrorCodes:
    """Test all error code ranges map to correct exception types."""

    @pytest.mark.parametrize(
        "errorno,expected_exception",
        [
            (5, EasyTransValidationError),  # JSON error
            (10, EasyTransAuthError),  # No username
            (12, EasyTransAuthError),  # Invalid credentials
            (15, EasyTransAuthError),  # API not active
            (18, EasyTransAuthError),  # Account disabled
            (20, EasyTransOrderError),  # Date/time error
            (22, EasyTransOrderError),  # Unknown productno
            (25, EasyTransOrderError),  # Unknown carrierno
            (30, EasyTransDestinationError),  # Min 2 destinations
            (33, EasyTransDestinationError),  # Unknown country
            (36, EasyTransDestinationError),  # Country not allowed
            (40, EasyTransPackageError),  # Unknown collect_destinationno
            (44, EasyTransPackageError),  # Unknown ratetypeno
            (50, EasyTransCustomerError),  # No company_name
            (54, EasyTransCustomerError),  # Customer already exists
            (60, EasyTransCustomerError),  # Username in use
        ],
    )
    @responses.activate
    def test_error_code_mapping(self, client, sample_order, errorno, expected_exception):
        """Test that each error code maps to the correct exception type."""
        error_response = {
            "error": {
                "errorno": errorno,
                "error_description": f"Test error {errorno}",
            }
        }

        responses.add(
            responses.POST,
            "https://mytrans.nl/demo/import_json.php",
            json=error_response,
            status=200,
        )

        with pytest.raises(expected_exception) as exc_info:
            client.import_orders([sample_order])

        assert str(errorno) in str(exc_info.value)
