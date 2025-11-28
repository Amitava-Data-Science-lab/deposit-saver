from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class HousingGoalState(BaseModel):
    status: Literal["success", "error"]
    postcode: Optional[str] = None
    property_type: Optional[str] = None
    house_price: Optional[float] = None
    deposit: Optional[float] = None
    error_message: Optional[str] = None


class CapacityState(BaseModel):
    status: Literal["success", "error"]
    suggested_investment: Optional[int] = None
    avg_surplus: Optional[float] = None
    median_surplus: Optional[float] = None
    error_message: Optional[str] = None


class RiskProfileState(BaseModel):
    status: Literal["success", "error"]
    risk_band: int
    max_equity_share: Optional[float] = None
    score_details: Optional[dict] = None  # or a more specific model
    profile_summary: Optional[str] = None
    error_message: Optional[str] = None


class PlanState(BaseModel):
    status: Literal["ok", "error"]
    feasibility: Optional[dict] = None   # {likelihood, min_final_value, max_final_value}
    plan: Optional[dict] = None          # {monthly_total, cash_contrib, etc.}
    user_explanation: Optional[str] = None
    error_message: Optional[str] = None


class SessionState(BaseModel):
    # Where in the flow we are
    stage: Literal["start", "housing", "bank", "risk", "planning", "done"] = "start"

    # Sub-agent outputs
    housing_goal: Optional[HousingGoalState] = None
    bank_capacity: Optional[CapacityState] = None
    risk_profile: Optional[RiskProfileState] = None
    final_plan: Optional[PlanState] = None

    # Any free-form notes or metadata
    notes: Optional[dict] = None

class HousingGoalInput(BaseModel):
    postcode: str
    property_type: str
   


class BankDataInput(BaseModel):
    file_content: str


class RiskProfileInput(BaseModel):
    income_stability: int 
    time_horizon_years: int 
    loss_reaction: int


class RiskProfileOutput(BaseModel):
    status: Literal["success", "error"]
    risk_band: int
    risk_band_text: str
    score_details: RiskProfileInput
    profile_summary: str
    max_equity_share: float

class PlanInput(BaseModel):
    housing_goal: HousingGoalState
    saving_capacity: CapacityState
    risk_profile: RiskProfileOutput


class PlanOutput(BaseModel):
    time_horizon_years: int
    suggested_investment: float
    risk_band: int
    max_equity_share: float
