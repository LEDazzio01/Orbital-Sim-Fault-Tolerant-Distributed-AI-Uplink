import pytest
import math
from src.core.thermal import RadiatorSystem, ThermalConfig, ThermalThrottlingException

# Citation: Starcloud White Paper, Page 9, Eq 1 
# "A radiator held at 20°C will radiate heat... according to Stefan-Boltzmann law... 385.24 W/m^2"
def test_stefan_boltzmann_accuracy():
    """
    Validates that the code matches the specific physics example 
    provided in the Starcloud White Paper.
    """
    config = ThermalConfig(
        surface_area_m2=1.0,
        emissivity=0.92,
        initial_temp_k=293.15, # 20°C
        mass_kg=50.0 # Standard mass
    )
    radiator = RadiatorSystem(config)
    
    # Calculate rejection
    watts_out = radiator.calculate_rejection_watts()
    
    # The White Paper states ~385.24 W per side. 
    # We check if we are within 1% margin of error.
    expected_watts = 385.24
    assert math.isclose(watts_out, expected_watts, rel_tol=0.01), \
        f"Physics Error: Expected ~{expected_watts}W rejection, got {watts_out}W"

def test_system_cools_down():
    """Verifies that with 0 load, the temperature drops."""
    radiator = RadiatorSystem()
    start_temp = radiator.current_temp_k
    
    # Tick for 60 seconds with 0 Watts load
    radiator.tick(load_watts=0, dt_seconds=60)
    
    assert radiator.current_temp_k < start_temp, \
        "Thermodynamics Failure: System did not cool down in vacuum with 0 load."

def test_overheating_trip():
    """
    Chaos Test: Pump massive heat into the system and ensure 
    it triggers the ThermalThrottlingException at 80°C.
    """
    # Configure a small system so it heats up fast
    config = ThermalConfig(mass_kg=10.0, max_temp_k=353.15) # Trip at 80°C
    radiator = RadiatorSystem(config)
    
    # Apply 5000 Watts (massive overload) continuously
    with pytest.raises(ThermalThrottlingException) as excinfo:
        # Loop until it explodes or we hit a timeout
        for _ in range(1000):
            radiator.tick(load_watts=5000.0, dt_seconds=1.0)
            
    # Check the exception message contains the temperature
    assert "OVERHEAT WARNING" in str(excinfo.value)