"""
Property & Energy Consumption Pydantic Schemas
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


PropertyTypeEnum = Literal["detached", "semi_detached", "terraced", "flat"]
EnergyRatingEnum = Literal["A", "B", "C", "D", "E", "F", "G"]
InsulationEnum = Literal["poor", "average", "good"]
HeatingEnum = Literal["gas_boiler", "electric_resistive", "oil_boiler", "heat_pump"]
GlazingEnum = Literal["single", "double", "triple"]
SolarEnum = Literal["none", "2kw", "4kw"]


class MonthlyEnergyRecord(BaseModel):
    month: int = Field(..., ge=1, le=12, description="Month of year (1-12)")
    electricity_kwh: Optional[float] = Field(None, ge=0, description="Metered electricity import (kWh)")
    gas_kwh: Optional[float] = Field(None, ge=0, description="Metered gas consumption (kWh)")


class PropertyInput(BaseModel):
    property_id: str = Field(..., example="P10001", description="Unique UK property identifier")
    customer_id: Optional[str] = Field("C0001", example="C0001", description="UK customer identifier")
    property_type: PropertyTypeEnum = Field("semi_detached", description="UK residential dwelling type")
    age: int = Field(1975, ge=1800, le=2026, description="Year of property construction")
    floor_area_m2: float = Field(..., gt=10.0, lt=1000.0, example=95.0, description="Total internal floor area in m2")
    region: str = Field("South East", description="UK geographic region")
    bedrooms: int = Field(3, ge=1, le=10, description="Number of bedrooms")
    energy_rating: EnergyRatingEnum = Field("E", description="Standard UK EPC energy band (A to G)")
    insulation: InsulationEnum = Field("poor", description="Insulation standard (poor, average, good)")
    heating: HeatingEnum = Field("gas_boiler", description="Primary space and water heating system")
    glazing: GlazingEnum = Field("single", description="Glazing type (single, double, triple)")
    solar: SolarEnum = Field("none", description="Existing rooftop solar generation")
    smart_controls: bool = Field(False, description="Whether smart thermostat / smart zoning installed")
    current_property_value_gbp: Optional[float] = Field(325000.0, gt=10000.0, description="Estimated current market property valuation in GBP")
    
    # Metered data input: Either annual directly, or monthly records
    annual_electricity_kwh: Optional[float] = Field(None, ge=0, description="Annual metered electricity (kWh/year)")
    annual_gas_kwh: Optional[float] = Field(None, ge=0, description="Annual metered gas (kWh/year)")
    monthly_records: Optional[List[MonthlyEnergyRecord]] = Field(default=None, description="Monthly meter observations (if available)")

    @model_validator(mode="after")
    def validate_energy_and_rating_consistency(self):
        # Clean string formats
        if isinstance(self.energy_rating, str):
            self.energy_rating = self.energy_rating.upper()  # type: ignore
        return self


class PropertySummary(BaseModel):
    property_id: str
    customer_id: Optional[str]
    property_type: str
    age: int
    floor_area_m2: float
    region: str
    bedrooms: int
    energy_rating: str
    insulation: str
    heating: str
    glazing: str
    solar: str
    smart_controls: bool
    current_property_value_gbp: Optional[float]
    annual_electricity_kwh: float
    annual_gas_kwh: float
    total_purchased_energy_kwh: float
    energy_intensity_kwh_m2: float
    data_quality_flags: List[str]
