"""
Application Configuration and Core Constants
Lloyds Megathon X PS2: Green Home Score & Retrofit Recommendation Engine
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://localhost:3010,http://127.0.0.1:3010,http://localhost:3020,http://127.0.0.1:3020"

    # Optional Supabase PostgreSQL credentials
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str = ""

    # Optional Gemini LLM Explanation Layer
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # UK DESNZ / DEFRA Official GHG Conversion Factors (kg CO2e per kWh)
    # Source: UK Government GHG Conversion Factors for Company Reporting 2024
    ELECTRICITY_EMISSION_FACTOR_KG: float = 0.20707
    GAS_EMISSION_FACTOR_KG: float = 0.18254
    EMISSION_FACTORS_YEAR: int = 2024
    EMISSION_FACTORS_SOURCE: str = "UK DESNZ / DEFRA GHG Conversion Factors 2024 (Scope 1 Natural Gas, Scope 2 Electricity Grid)"

    # Fixed weights for the 7 Green Home Score components (sum = 1.00)
    WEIGHT_ENERGY_EFFICIENCY: float = 0.25
    WEIGHT_CONSUMPTION_INTENSITY: float = 0.20
    WEIGHT_INSULATION: float = 0.15
    WEIGHT_HEATING_SYSTEM: float = 0.15
    WEIGHT_GLAZING: float = 0.10
    WEIGHT_RENEWABLES: float = 0.10
    WEIGHT_SMART_CONTROLS: float = 0.05

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
