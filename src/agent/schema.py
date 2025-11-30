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
    status: Optional[str] = None
    postcode: Optional[str] = None
    property_type: Optional[str] = None    
    # Final confirmed price and target
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    house_price: Optional[float] = None
    deposit_target: Optional[float] = None    
    # List of options returned by the price search tool
    price_ranges: Optional[list[PropertyPrice]] = None 
    message: Optional[str] = None
    


class CapacityState(BaseModel):
    status: Optional[str] = None
    suggested_investment: Optional[int] = None
    average_surplus: Optional[float] = None
    median_surplus: Optional[float] = None
    is_affordable: Optional[bool] = None
    max_affordability: Optional[float] = None
    message: Optional[str] = None



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
    income_stability: Optional[int] = None
    time_horizon_years: Optional[int] = None
    loss_reaction: Optional[int] = None


class RiskProfileOutput(BaseModel):
    status: Optional[str] = None
    risk_band: Optional[int] = None
    risk_band_text: Optional[str] = None
    score_details: RiskProfileInput = None
    profile_summary: Optional[str] = None
    max_equity_share: Optional[float] = None 

class PlanInput(BaseModel):
    postcode: Optional[str] = None
    property_type: Optional[str] = None    
    deposit_target: Optional[float] = None 
    available_investment: Optional[float] = None
    income_stability: Optional[int] = None
    time_horizon_years: Optional[int] = None
    loss_reaction: Optional[int] = None
    risk_band: Optional[int] = None
    max_equity_share: Optional[float] = None 

class PlanOutput(BaseModel):
    time_horizon_years: Optional[float] = None
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

    