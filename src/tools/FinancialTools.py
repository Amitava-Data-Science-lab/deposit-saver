import logging
from datetime import datetime
from enum import Enum
from typing import List
from io import StringIO
import numpy as np
import pandas as pd
from src.agent.schema import PlanInput


logger = logging.getLogger(__name__)

BASE_GROWTH_RATE = 0.03
LOW_GROWTH_RATE = 0.04
MODERATE_GROWTH_RATE = 0.06
HIGH_GROWTH_RATE = 0.08


class TransactionType(Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class Transaction:
    def __init__(self, date, amount, transaction_type):
        """
        Initialize a Transaction object.

        Args:
            date (datetime or str): Transaction date
            amount (float): Transaction amount
            transaction_type (TransactionType or str): 'credit' or 'debit'
        """
        if isinstance(date, str):
            self.date = datetime.fromisoformat(date)
        else:
            self.date = date

        self.amount = float(amount)

        if isinstance(transaction_type, str):
            self.transaction_type = TransactionType(transaction_type.lower())
        else:
            self.transaction_type = transaction_type

    def __repr__(self):
        return f"Transaction(date={self.date.date()}, amount={self.amount}, type={self.transaction_type.value})"

    def is_credit(self):
        return self.transaction_type == TransactionType.CREDIT

    def is_debit(self):
        return self.transaction_type == TransactionType.DEBIT

def estimate_affordability(file_content: str, house_price: float) -> dict:
    """
    Analyzes transactions from a bank statement to estimate monthly surplus and provide estimate of investable funds.

    Args:
        file_content (str): Contents of the bank statement CSV file.List[Transaction]): A list of Transaction objects containing financial data.
        house_price: The estimated house price for the property   
    Returns:
        dict: A dictionary containing the following keys:
            - status: "error" or "success" indicating the analysis status
            - message: Error or status message (e.g., "no transactions found", "not enough transactions...")
            - available_investment: 80% of median monthly surplus (conservative estimate for safe investing)
            - average_surplus: Mean of all monthly surpluses across the period
            - median_surplus: Middle value of monthly surpluses (less affected by outliers)
            - average_income : Mean of all the monthly income across the period
            - median_income : Median of all the monthly income across the period
            - is_affordable: Indicates if the house price is affordable based on the income.
            - max_affordability: Maximum value of the mortgage that a bank will approve.


    Note:
        The function handles errors gracefully by returning a dictionary with status "error"
        and an appropriate error message rather than raising exceptions.

    Example Usage:
        >>> from datetime import datetime
        >>> transactions = [
        ...     Transaction("2025-01-15", 3000.0, "credit"),
        ...     Transaction("2025-01-20", 1500.0, "debit"),
        ...     Transaction("2025-02-15", 3200.0, "credit"),
        ...     Transaction("2025-02-25", 1400.0, "debit"),
        ...     Transaction("2025-03-10", 3100.0, "credit"),
        ...     Transaction("2025-03-18", 1600.0, "debit")
        ... ]
        >>> suggested, avg, median, low = estimate_surplus(transactions)
        >>> print(f"Suggested monthly investment: ${suggested:.2f}")
        >>> print(f"Average monthly surplus: ${avg:.2f}")
        >>> print(f"Median monthly surplus: ${median:.2f}")
        >>> print(f"Lowest monthly surplus: ${low:.2f}")

    LLM Tool Usage Guidelines:
        When calling this function:
        1. Ensure you have a valid list of Transaction objects with dates, amounts, and types
        2. Transactions should span multiple months for meaningful analysis
        3. Use the available_investment value for conservative financial planning
        4. Compare low_surplus against available_investment to validate safety margin
        5. If median differs significantly from average, investigate outlier months
    """

    AFFORABILITY_MULTIPLIER = 80

    output = {
        "status": "error",
        "message": "no transactions found",
        "available_investment": 0.0,
        "average_surplus": 0.0,
        "median_surplus": 0.0,
        "average_income": 0.0,
        "median_income": 0.0,
        "max_affordability": 0.0,
        "is_affordable": False
    }

    try:
        logger.info(f"Starting affordability Estimate with house price: {house_price}")
        df = pd.read_csv(StringIO(file_content))

        if df.empty:
            logger.warning("No transactions provided to estimate_surplus")
            return output
        
        df.fillna(0, inplace=True)
        df["Transaction Date"] = pd.to_datetime(df["Transaction Date"])
        df["month"] = df["Transaction Date"].dt.to_period("M").astype(str)
        distinct_months = df["month"].unique()
        if distinct_months.size < 3:
            logger.warning(f"Insufficient transaction months {distinct_months.size}: need at least 3")
            output["message"] = "not enough transactions to estimate surplus, Please provide at least 3 months of transactions"
            return output

        monthly = (
            df.groupby("month")[["Credit amount", "Debit amount"]]
            .sum()
            .reset_index()
        )
        logger.info("Calculating monthly aggregates")
        monthly["surplus"] = monthly["Credit amount"] - monthly["Debit amount"]
        output["average_income"] = round(monthly["Credit amount"].mean())
        output["median_income"] = round(monthly["Credit amount"].median())
        output["average_surplus"] = round(monthly["surplus"].mean())
        output["median_surplus"] = round(monthly["surplus"].median())
        output["available_investment"] = round(np.min([0.8 * output["median_surplus"], output["average_surplus"]]))
        output["status"] = "success"
        output["message"] = "Available Investment estimated successfully"

        max_loan_amount = output["median_income"]*AFFORABILITY_MULTIPLIER
        logger.info(f"Max loan amount: {max_loan_amount}")
        if (max_loan_amount > house_price):
            is_affordable = True
        else:
            is_affordable = False

        output["is_affordable"] = is_affordable
        output["max_affordability"] = output["median_income"]*AFFORABILITY_MULTIPLIER

        if not is_affordable:
            output["status"] = "success"
            output["message"] = f"""Based on your income estimates from the bank statement the average house 
            price of {house_price} is outside your afforable range of {output["median_income"]*5} """
            logger.info(f"Affordablility output: {output}")
            return output

        logger.info(f"Surplus estimation successful - available_investment: {output['available_investment']}, average: {output['average_surplus']}, median: {output['median_surplus']}")
        return output

    except AttributeError as e:
        logger.error(f"AttributeError in estimate_surplus: {e}")
        output["message"] = f"Invalid transaction object: missing required attributes (date, amount, or transaction type)"
        return output
    except (TypeError, ValueError) as e:
        logger.error(f"TypeError/ValueError in estimate_surplus: {e}")
        output["message"] = f"Invalid data format in transactions"
        return output
    except Exception as e:
        logger.error(f"Unexpected error in estimate_surplus: {e}")
        output["message"] = f"Unexpected error during surplus estimation"
        return output 

def deposit_calculator(min_value: float, max_value: float, deposit_percent: float) -> dict:
    """
    Calculate the deposit amount based on house price and deposit percentage.

    Args:
        min_price: minimum value of the house price
        max_price: maximum value of the house price
        deposit_percent: The percentage of house price to use as deposit (default 0.1 for 10%)

    Returns:
        1. Deposit Amount: Amount of deposit needed.
        2. House Price: Estimated house price to target.
    """
    
    logger.info(f"Starting deposit calculation - min_value: {min_value}, max_value: {max_value}, deposit_percent: {deposit_percent}")
    house_price = np.ceil(min_value + (max_value - min_value) / 5 ) ## Little bit higher than mon value
    logger.info(f"Calculating deposit for house_price of {house_price} with  deposit_percent={deposit_percent}")
    deposit = np.ceil(house_price * deposit_percent)
    logger.info(f"Calculated deposit: {deposit}")
    
    return {
        "deposit_amount": deposit,
        "house_price": house_price
    }
    
def feasibility_calculator(planInput: PlanInput):
    """
    Calculate the feasibility of reaching a deposit goal based on monthly savings, investment growth, and risk tolerance.

    Args:
        PlanInput: Input to the plan generator step
        

    Returns:
        dict: A dictionary containing:
            - min_value (float): Minimum projected value based on risk tolerance                
            - max_value (float): Maximum projected value based on risk tolerance               
            - likelihood (str): Feasibility assessment
                - "feasible": Deposit goal can be met with minimum projection
                - "tight": Deposit goal is achievable but requires favorable conditions
                - "infeasible": Deposit goal cannot be met even with high growth
            - years_to_target (int): number of years to acheive the target in current circumstances
            - User Input: Return the plan input that was passed to this function.

    Growth Rate Constants:
        - LOW_GROWTH_RATE: 3% annual return (conservative investments)
        - MODERATE_GROWTH_RATE: 5% annual return (balanced portfolio)
        - HIGH_GROWTH_RATE: 7% annual return (aggressive investments)

    Example:
        >>> result = feasibility_calculator(
        ...     saving=1000.0,
        ...     deposit=50000.0,
        ...     property_price=500000.0,
        ...     risk_band="moderate",
        ...     time_horizon=5
        ... )
        >>> print(f"Min value: ${result['min_value']:.2f}")
        >>> print(f"Max value: ${result['max_value']:.2f}")
        >>> print(f"Likelihood: {result['likelihood']}")

    Note:
        The function uses compound interest formula: FV = PMT * ((1 + r)^n - 1) / r
        where PMT is the monthly saving, r is the monthly growth rate, and n is total months.
    """
    
    ## Extract required variables
    available_investment = planInput.saving_capacity.suggested_investment
    deposit = planInput.housing_goal.deposit
    risk_band = planInput.risk_profile.risk_band
    time_horizon = planInput.risk_profile.score_details.time_horizon_years

    logger.info(f"Starting feasibility calculation - available_investment: {available_investment}, deposit: {deposit}, risk_band: {risk_band}, time_horizon: {time_horizon} years")

    ## Calculate growth rates

    r_month_base = pow(1 + BASE_GROWTH_RATE, 1/12) - 1
    r_month_low = pow(1 + LOW_GROWTH_RATE, 1/12) - 1
    r_month_moderate = pow(1 + MODERATE_GROWTH_RATE, 1/12) - 1
    r_month_high = pow(1 + HIGH_GROWTH_RATE, 1/12) - 1

    logger.info(f"Monthly growth rates - base: {r_month_base:.6f}, low: {r_month_low:.6f}, moderate: {r_month_moderate:.6f}, high: {r_month_high:.6f}")

    base_value = available_investment*(pow(1+r_month_base, 12*time_horizon) -1)/r_month_base
    low_value = available_investment*(pow(1+r_month_low, 12*time_horizon) -1)/r_month_low
    high_value = available_investment*(pow(1+r_month_high, 12*time_horizon) -1)/r_month_high
    avg_value = available_investment*(pow(1+r_month_moderate, 12*time_horizon) -1)/r_month_moderate

    logger.info(f"Projected values - base: {base_value:.2f}, low: {low_value:.2f}, moderate: {avg_value:.2f}, high: {high_value:.2f}")

    min_value = available_investment*12*time_horizon
    max_value = available_investment*12*time_horizon
    years_to_target = time_to_savings(available_investment, deposit, r_month_base)
    if risk_band == 1:
        logger.info(f"Risk Band 1 (No Risk) - Using base growth rate: {r_month_base:.6f}")
        max_value = base_value
        logger.info(f"Risk Band 1 final values - min: {min_value:.2f}, max: {max_value:.2f}")
    elif risk_band == 2:
        logger.info(f"Risk Band 2 (Low Risk) - Using low growth rate: {r_month_low:.6f}")
        min_value = base_value
        max_value = low_value
        years_to_target = time_to_savings(available_investment, deposit, r_month_low)
        logger.info(f"Risk Band 2 final values - min: {min_value:.2f}, max: {max_value:.2f}, years_to_target: {years_to_target}")
    elif risk_band == 3:
        logger.info(f"Risk Band 3 (Moderate Risk) - Using moderate growth rate: {r_month_moderate:.6f}")
        min_value = low_value
        max_value = avg_value
        years_to_target = time_to_savings(available_investment, deposit, r_month_moderate)
        logger.info(f"Risk Band 3 final values - min: {min_value:.2f}, max: {max_value:.2f}, years_to_target: {years_to_target}")
    elif risk_band >= 4:
        logger.info(f"Risk Band 4+ (High Risk) - Using high growth rate: {r_month_high:.6f}")
        min_value = avg_value
        max_value = high_value
        years_to_target = time_to_savings(available_investment, deposit, r_month_high)
        logger.info(f"Risk Band 4 final values - min: {min_value:.2f}, max: {max_value:.2f}, years_to_target: {years_to_target}")

    goal = "tight"
    if deposit <= min_value:
        goal = "feasible"
        logger.info(f"Goal assessment: FEASIBLE (deposit {deposit:.2f} <= min_value {min_value:.2f})")
    elif high_value < deposit:
        goal = "infeasible"
        logger.info(f"Goal assessment: INFEASIBLE (high_value {high_value:.2f} < deposit {deposit:.2f})")
    else:
        logger.info(f"Goal assessment: TIGHT (deposit {deposit:.2f} between min {min_value:.2f} and max {max_value:.2f})")

    result = {
        "status": "ok",
        "min_final_value": round(min_value),
        "max_final_value": round(max_value),
        "likelihood": goal,
        "years_to_target": years_to_target,
        "user_input": planInput
        
    }

    logger.info(f"Feasibility calculation complete - Result: {result}")
    return result

def time_to_savings(saving_per_month: float, target_deposit: float, monthly_rate:float) -> int:

   n_months = np.log(1 + (target_deposit * monthly_rate) / saving_per_month) / np.log(1 + monthly_rate)
   return np.ceil(n_months/12).astype(int)

def risk_classification(income_stability: int, time_horizon_years: int, loss_reaction: int):
    """
    Classify an investor's risk profile and determine appropriate equity allocation based on financial circumstances and risk tolerance.

    This function evaluates three key factors to determine an appropriate investment risk band and maximum equity exposure:
    income stability, investment time horizon, and emotional reaction to potential losses.

    Args:
        income_stability (int): Stability of the investor's income stream. Scale 1-5:
            - 1-2: Unstable/irregular income (freelance, commission-based, uncertain employment)
            - 3: Moderate stability (stable job but single income source)
            - 4-5: High stability (dual income, secure employment, diverse income streams)
        time_horizon_years (int): Number of years until the invested funds will be needed.
            - ≤3 years: Short-term (limited time to recover from losses)
            - 4-6 years: Medium-term
            - ≥7 years: Long-term (sufficient time to ride out market volatility)
        loss_reaction (int): Investor's emotional tolerance for investment losses. Scale 1-5:
            - 1: Would panic and sell immediately if portfolio dropped 10%
            - 2: Would be very concerned but might hold on
            - 3: Would be uncomfortable but understand it's part of investing
            - 4-5: Would stay calm or see it as a buying opportunity

    Returns:
        dict: A dictionary containing:
            - risk_band (str): Risk classification level as a string:
                - "1": No Risk - Savings/cash only (0% equity)
                - "2": Low Risk - Very conservative (up to 20% equity)
                - "3": Moderate Risk - Balanced approach (up to 50% equity)
                - "4": High Risk - Growth-focused (up to 70% equity)
            - risk_band_Text (str): Human-readable description of the risk band
            - max_equity_share (float): Maximum recommended equity allocation as a decimal (0.0 to 0.70)
    """
    logger.info(f"Starting risk classification - income_stability: {income_stability}, time_horizon_years: {time_horizon_years}, loss_reaction: {loss_reaction}")

    risk_bank = "1"
    risk_band_text = "No Risk"
    max_equity_share = 0.0

    if (loss_reaction == 1) or (time_horizon_years <= 3) or (income_stability <= 2):
        risk_bank = "1"
        risk_band_text = "No Risk"
        max_equity_share = 0.0
        logger.info(f"Classified as No Risk (Band 1) - Criteria: loss_reaction={loss_reaction}, time_horizon={time_horizon_years}, income_stability={income_stability}")
    elif (loss_reaction == 2) or (time_horizon_years <= 3) or (income_stability <= 2):
        risk_bank = "2"
        risk_band_text = "Low Risk"
        max_equity_share = 0.2
        logger.info(f"Classified as Low Risk (Band 2) - max_equity_share: {max_equity_share}")
    elif (loss_reaction >= 4) or (time_horizon_years >= 7) or (income_stability >= 3):
        risk_bank = "4"
        risk_band_text = "High Risk"
        max_equity_share = 0.70
        logger.info(f"Classified as High Risk (Band 4) - max_equity_share: {max_equity_share}")
    else:
        risk_bank = "3"
        risk_band_text = "Moderate Risk"
        max_equity_share = 0.50
        logger.info(f"Classified as Moderate Risk (Band 3) - max_equity_share: {max_equity_share}")

    result = {
        "risk_band": risk_bank,
        "risk_band_Text": risk_band_text,
        "max_equity_share": max_equity_share,
    }

    logger.info(f"Risk classification complete - Result: {result}")
    return result
    

