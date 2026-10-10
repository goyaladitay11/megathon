"""
Retrofit Catalogue & Domain Definitions
Documented according to Lloyds Megathon X Problem Statement 2 (Section 4 & 5)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RetrofitItem(BaseModel):
    id: str
    name: str
    category: str
    indicative_impact_description: str
    space_heating_reduction_pct: float = Field(0.0, description="Reduction on space heating load (0.0 to 1.0)")
    grid_import_reduction_pct: float = Field(0.0, description="Reduction on electricity grid imports (0.0 to 1.0)")
    heat_pump_cop: float = Field(3.0, description="Seasonal Coefficient of Performance for heat pump")
    typical_cost_min_gbp: float
    typical_cost_max_gbp: float
    typical_cost_avg_gbp: float
    priority_order: int
    prerequisite_ids: List[str] = Field(default_factory=list)
    source_documentation: str


RETROFIT_CATALOGUE: Dict[str, RetrofitItem] = {
    "roof_insulation": RetrofitItem(
        id="roof_insulation",
        name="Roof or Loft Insulation (270mm+)",
        category="Insulation",
        indicative_impact_description="12–18% reduction in space-heating energy demand",
        space_heating_reduction_pct=0.15,  # Midpoint of 12-18%
        grid_import_reduction_pct=0.0,
        typical_cost_min_gbp=600.0,
        typical_cost_max_gbp=1200.0,
        typical_cost_avg_gbp=900.0,
        priority_order=1,
        prerequisite_ids=[],
        source_documentation="Energy Saving Trust UK & Lloyds PS2 Section 4: 12-18% space-heating reduction.",
    ),
    "double_glazing": RetrofitItem(
        id="double_glazing",
        name="High-Performance Double Glazing",
        category="Glazing",
        indicative_impact_description="8–12% reduction in space-heating energy demand",
        space_heating_reduction_pct=0.10,  # Midpoint of 8-12%
        grid_import_reduction_pct=0.0,
        typical_cost_min_gbp=3500.0,
        typical_cost_max_gbp=7500.0,
        typical_cost_avg_gbp=5500.0,
        priority_order=2,
        prerequisite_ids=[],
        source_documentation="Energy Saving Trust UK & Lloyds PS2 Section 4: 8-12% space-heating demand reduction.",
    ),
    "smart_thermostat": RetrofitItem(
        id="smart_thermostat",
        name="Smart Thermostat & Heating Controls",
        category="Smart Controls",
        indicative_impact_description="5–10% reduction in heating energy use",
        space_heating_reduction_pct=0.075,  # Midpoint of 5-10%
        grid_import_reduction_pct=0.0,
        typical_cost_min_gbp=200.0,
        typical_cost_max_gbp=350.0,
        typical_cost_avg_gbp=250.0,
        priority_order=3,
        prerequisite_ids=[],
        source_documentation="BEIS / DESNZ Smart Thermostat trials & Lloyds PS2 Section 4: 5-10% heating reduction.",
    ),
    "heat_pump": RetrofitItem(
        id="heat_pump",
        name="Air Source Heat Pump (ASHP)",
        category="Heating",
        indicative_impact_description="Replaces gas heating with SPF 3.0 electric heat pump; displaces gas, increases electric imports, achieving 15–25% net purchased energy reduction",
        space_heating_reduction_pct=0.0,
        grid_import_reduction_pct=0.0,
        heat_pump_cop=3.0,  # Seasonal Performance Factor ~3.0
        typical_cost_min_gbp=8000.0,
        typical_cost_max_gbp=14000.0,
        typical_cost_avg_gbp=10500.0,
        priority_order=4,
        prerequisite_ids=["roof_insulation"],  # Fabric-first rule: ensure insulation is addressed
        source_documentation="MCS Heat Pump Standards & Lloyds PS2 Section 4 & 5: 15-25% purchased energy reduction with fuel switching.",
    ),
    "solar_pv": RetrofitItem(
        id="solar_pv",
        name="Rooftop Solar PV Array (3.5 - 4.0 kWp)",
        category="Renewables",
        indicative_impact_description="20–35% reduction in grid electricity imports (floored at 0, does not reduce underlying home demand)",
        space_heating_reduction_pct=0.0,
        grid_import_reduction_pct=0.28,  # Midpoint of 20-35%
        typical_cost_min_gbp=5000.0,
        typical_cost_max_gbp=8500.0,
        typical_cost_avg_gbp=6500.0,
        priority_order=5,
        prerequisite_ids=[],
        source_documentation="MCS Solar PV Guidance & Lloyds PS2 Section 4: 20-35% grid import reduction.",
    ),
}
