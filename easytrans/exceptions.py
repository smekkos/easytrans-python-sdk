"""
Exception classes for EasyTrans SDK.

All exceptions inherit from EasyTransError base class.
Specific exception types are raised based on API error codes (errorno).
"""


class EasyTransError(Exception):
    """Base exception for all EasyTrans SDK errors."""

    pass


class EasyTransAPIError(EasyTransError):
    """HTTP/network communication errors."""

    pass


class EasyTransAuthError(EasyTransError):
    """
    Authentication and authorization errors.
    
    Error codes: 10-19
    - 10: No username given
    - 11: No password given
    - 12: Invalid username or password
    - 13: Unknown mode
    - 14: Unknown type
    - 15: API not active
    - 16: User account cannot import customers
    - 17: Unknown return_documents type
    - 18: Account disabled
    - 19: Invalid user rights
    """

    pass


class EasyTransValidationError(EasyTransError):
    """
    Generic validation errors.
    
    Error code: 5 (JSON parsing errors)
    """

    pass


class EasyTransOrderError(EasyTransError):
    """
    Order-specific validation errors.
    
    Error codes: 20-29
    - 20: Incorrect date or time values
    - 21: No productno given
    - 22: Unknown productno
    - 23: No customerno given (when required)
    - 24: Unknown customerno
    - 25: Unknown carrierno
    - 26: Unknown vehicleno
    - 27: Unknown status
    - 28: Unknown carrier_service
    - 29: No carrier_service allowed
    - 210: Unknown carrier_options
    - 211: No carrier_options allowed
    - 213: Customer not active
    - 214: Unknown fleetno
    - 215: Unknown substatusno
    """

    pass


class EasyTransDestinationError(EasyTransError):
    """
    Destination-specific validation errors.
    
    Error codes: 30-39
    - 30: Minimum of two destinations required
    - 31: Incorrect destinationno
    - 32: Incorrect collect_deliver value
    - 33: Unknown or disabled country
    - 34: Incorrect delivery date or time
    - 35: Incorrect delivery from time
    - 36: Country cannot be used with product
    - 37: Invalid number of documents per destination
    - 38: Unknown document type
    - 39: Invalid base64_content
    - 310: base64_content too large
    """

    pass


class EasyTransPackageError(EasyTransError):
    """
    Package/goods-specific validation errors.
    
    Error codes: 40-45
    - 40: Unknown collect_destinationno (not exist)
    - 41: Unknown collect_destinationno (not a collect destination)
    - 42: Unknown deliver_destinationno (not exist)
    - 43: Unknown deliver_destinationno (not a deliver destination)
    - 44: Unknown ratetypeno
    - 45: Weight required (for GLS shipments)
    """

    pass


class EasyTransCustomerError(EasyTransError):
    """
    Customer-specific validation errors.
    
    Error codes: 50-65
    - 50: No company_name given
    - 51: Unknown or disabled country
    - 52: Unknown or disabled mail_country
    - 53: customerno must be numeric
    - 54: customerno already exists
    - 55: Invalid language
    - 56: Invalid payment method
    - 57: external_id already exists
    - 58: external_id already assigned
    - 60: Username already in use
    - 61: Username too long
    - 62: No password given (when required)
    - 63: Password too short
    - 65: Unknown userid
    """

    pass
