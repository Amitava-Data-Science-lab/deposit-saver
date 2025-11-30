from io import StringIO
import logging
import pandas as pd
import os
from typing import Dict, Any
from src.tools.ErrorAndStatus import StatusCodes, BankFileErrorCode

logger = logging.getLogger(__name__)


def load_bank_statement(file_content: str) -> Dict[str, Any]:
    """
    Load and validate a bank statement CSV file.

    Args:
        file_content (str): Contents of the bank statement CSV file.

    Returns:
        Dictionary containing:
            - status: "success" or StatusCodes.SUCCESS
            - error_code: Code identifying the specific error
            - message: Descriptive message about the operation
            - columns: List of column names if successful, None otherwise

    Expected CSV columns:
        - Transaction Date
        - Description
        - Credit amount
        - Debit amount
    """
    output = {
        "status": StatusCodes.ERROR,
        "message": "",
        "columns": None
    }

    try:
              
        # Load the CSV file
        logger.info(f"Reading CSV file:")
        df = pd.read_csv(StringIO(file_content ))
        df.fillna(0, inplace=True)
        logger.info(f"Successfully read CSV with {len(df)} rows")

        # Define required columns
        required_columns = [
            "Transaction Date",
            "Description",
            "Credit amount",
            "Debit amount"
        ]

        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            output["error_code"] = BankFileErrorCode.MISSING_COLUMNS
            output["message"] = f"Missing required columns: {missing_columns}. Found columns: {list(df.columns)}"
            logger.error(output["message"])
            return output

        # All validations passed
        output["status"] = StatusCodes.SUCCESS
        output["message"] = f"Successfully loaded CSV file with {len(df)} rows and {len(df.columns)} columns"
        output["columns"] = list(df.columns)

        logger.info(output["message"])
        logger.info(f"Columns found: {output['columns']}")

        return output

    except pd.errors.EmptyDataError:
        output["error_code"] = BankFileErrorCode.EmptyDataError
        output["message"] = "CSV file is empty"
        logger.error(output["message"])
        return output

    except pd.errors.ParserError as e:
        output["error_code"] = BankFileErrorCode.ParserError
        output["message"] = f"Error parsing CSV file: {str(e)}"
        logger.error(output["message"])
        return output

    except Exception as e:
        output["error_code"] = BankFileErrorCode.UNKNOWN_ERROR
        output["message"] = f"Unexpected error loading file: {str(e)}"
        logger.error(f"Unexpected error in load_bank_statement: {e}")
        return output
