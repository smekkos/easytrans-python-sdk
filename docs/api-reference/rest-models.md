# REST Models

Typed dataclass models returned by the REST API (`/api/v1/`) methods.

!!! tip "Date fields"
    Several models expose a raw `date: Optional[str]` field (format `YYYY-MM-DD`)
    alongside a computed `date_parsed: Optional[datetime.date]` property.
    Use `date_parsed` for arithmetic and comparisons; the raw string is preserved
    for serialisation and backward compatibility.

## PagedResponse

::: easytrans.rest_models.PagedResponse

## RestOrder

::: easytrans.rest_models.RestOrder

## RestOrderAttributes

::: easytrans.rest_models.RestOrderAttributes

## RestDestination

::: easytrans.rest_models.RestDestination

## RestTrackHistoryEntry

::: easytrans.rest_models.RestTrackHistoryEntry

## RestCustomer

::: easytrans.rest_models.RestCustomer

## RestCarrier

::: easytrans.rest_models.RestCarrier

## RestFleetVehicle

::: easytrans.rest_models.RestFleetVehicle

## RestInvoice

::: easytrans.rest_models.RestInvoice

## RestProduct

::: easytrans.rest_models.RestProduct

## RestPackageType

::: easytrans.rest_models.RestPackageType

## RestVehicleType

::: easytrans.rest_models.RestVehicleType

## RestSubstatus

::: easytrans.rest_models.RestSubstatus
