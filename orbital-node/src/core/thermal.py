import math
from pydantic import BaseModel, Field
from typing import Optional

# Constants derived from Starcloud White Paper
STEFAN_BOLTZMANN_SIGMA = 5.67e-8
DEEP_SPACE_TEMP_K = 3.0  # Effectively -270C

class ThermalConfig(BaseModel):
    """Configuration for the Satellite Radiator System."""
    mass_kg: float = Field(default=50.0, description="Total thermal mass of the node")
    specific_heat_j_kg_k: float = Field(default=900.0, description="Specific heat of Aluminum")
    surface_area_m2: float = Field(default=1.0, description="Radiator surface area")
    emissivity: float = Field(default=0.92, description="Efficiency of radiator coating")
    max_temp_k: float = Field(default=353.15, description="80C Safety Trip Limit")
    initial_temp_k: float = Field(default=293.15, description="Start at 20C")

class ThermalThrottlingException(Exception):
    """Raised when the system exceeds safe operating temperature."""
    pass

class RadiatorSystem:
    def __init__(self, config: Optional[ThermalConfig] = None):
        self.config = config or ThermalConfig()
        self.current_temp_k = self.config.initial_temp_k

    @property
    def current_temp_c(self) -> float:
        """Helper to get Temp in Celsius."""
        return self.current_temp_k - 273.15

    def calculate_rejection_watts(self) -> float:
        """
        Calculates heat radiated to deep space using Stefan-Boltzmann Law.
        P = ε * σ * A * (T_rad^4 - T_space^4)
        Reference White Paper Eq: P_emitted = 0.92 * 5.67e-8 * T^4
        """
        # We assume T_space is negligible compared to T_rad, but let's be precise.
        delta_t_4 = (self.current_temp_k**4) - (DEEP_SPACE_TEMP_K**4)
        
        power_radiated = (
            self.config.emissivity * STEFAN_BOLTZMANN_SIGMA * self.config.surface_area_m2 * delta_t_4
        )
        return power_radiated

    def tick(self, load_watts: float, dt_seconds: float = 1.0):
        """
        Physics Engine Loop.
        Updates temperature based on Heat In (Load) vs Heat Out (Radiator).
        """
        # 1. Calculate Cooling
        radiated_watts = self.calculate_rejection_watts()
        
        # 2. Calculate Net Heat (Joules per second)
        net_power = load_watts - radiated_watts
        
        # 3. Calculate Temp Change (Energy = Mass * SpecificHeat * DeltaT)
        # DeltaT = (Power * Time) / (Mass * SpecificHeat)
        thermal_mass = self.config.mass_kg * self.config.specific_heat_j_kg_k
        energy_joules = net_power * dt_seconds
        temp_delta = energy_joules / thermal_mass
        
        # 4. Update State
        self.current_temp_k += temp_delta

        # 5. Check Safety Constraints
        if self.current_temp_k >= self.config.max_temp_k:
            # In a real system, hardware protection trips here.
            # We simulate this by rejecting the job.
            raise ThermalThrottlingException(
                f"OVERHEAT WARNING: {self.current_temp_c:.2f}C exceeds limit {self.config.max_temp_k - 273.15}C"
            )

        return {
            "temp_c": self.current_temp_c,
            "radiated_watts": radiated_watts,
            "net_power": net_power
        }