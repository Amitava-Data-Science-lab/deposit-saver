from enum import Enum

class StatusCodes(str, Enum):
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    SUCCESS = "success"
    ERROR = "error"

class CommonErrorCodes(str, Enum):    
    TOOL_ERROR = "TOOL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INVALID_DATA = "INVALID_DATA"


class HousingErrorCode(str, Enum):
    INVALID_POSTCODE = "INVALID_POSTCODE"
    INVALID_PROPERTY_TYPE = "IINVALID_PROPERTY_TYPE"
    NO_PRICES_FOUND = "NO_PRICES_FOUND"
    MISSING_INPUT = "MISSING_INPUT"
    NO_NEARBY_CODES = "NO_NEARBY_CODES"

class BankFileErrorCode(str, Enum):
    EmptyDataError = "EmptyDataError"
    ParserError = "ParserError"
    MISSING_COLUMNS = "MISSING_COLUMNS"
    
    


class FeasibilityCode(str, Enum):
    FEASIBLE = "Feasible"
    TIGHT = "Tight"
    INFEASIBLE = "infeasible"