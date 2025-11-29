from typing import Optional, Literal
from pydantic import BaseModel, Field


class PropertyPrice(BaseModel):
    postCode: Optional[str] = None
    propertyType: Optional[str] = None
    type: Optional[str] = None
    bedrooms: Optional[int] = None
    priceMin: Optional[int] = None
    priceMax: Optional[int] = None
    sources: Optional[list[str]] = None

class HousingGoalState(BaseModel):
    status: Optional[str] = "error"
    postcode: Optional[str] = None
    property_type: Optional[str] = None    
    # Final confirmed price and target
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    deposit_target: Optional[float] = None    
    # List of options returned by the price search tool
    price_options: Optional[list[PropertyPrice]] = None # Renamed to avoid conflict
    
    error_message: Optional[str] = None


class CapacityState(BaseModel):
    status: Literal["success", "error"]
    suggested_investment: Optional[int] = None
    avg_surplus: Optional[float] = None
    median_surplus: Optional[float] = None
    error_message: Optional[str] = None

class HousingGoalInput(BaseModel):
    postcode: Optional[str] = None
    property_type: Optional[str] = None
    house_price: Optional[float] = None
    deposit_target: Optional[float] = None
    human_approval: Optional[bool] = False
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class BankDataInput(BaseModel):
    file_content: Optional[str] = None
    house_price: Optional[float] = None



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
    housing_goal: Optional[HousingGoalState] = None
    saving_capacity: Optional[CapacityState] = None
    risk_profile: Optional[RiskProfileOutput] = None


class PlanOutput(BaseModel):
    time_horizon_years: Optional[int] = None
    suggested_investment: Optional[float] = None
    risk_band: Optional[int] = None
    max_equity_share: Optional[float] = None

class WorkflowState(BaseModel):
    current_stage: Optional[str] = "housing"
    next_stage_to_address: Optional[str] = "housing"
    data_items_required_to_complete: Optional[list[str]] = None
    # Any free-form notes or metadata
    notes: Optional[str] = None



class SessionState(BaseModel):
    # Where in the flow we are
    stage: Literal["start", "housing", "capacity", "risk", "planning", "done"] = "start"

    # Sub-agent outputs
    housing_goal: Optional[HousingGoalState] = None
    bank_capacity: Optional[CapacityState] = None
    risk_profile: Optional[RiskProfileOutput] = None
    final_plan: Optional[PlanOutput] = None

    