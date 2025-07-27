import sys
import os
import pytest
import json
import math
from unittest.mock import patch, mock_open

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PCBDelayCalc import PCBDelayCalculator, generate_sdc_constraints, main

# --- Test Fixtures ---

@pytest.fixture(scope="module")
def materials_data():
    """Provides mock material data for tests."""
    return {
        "test_material": {
            "er": 4.0,
            "er_tolerance": 0.1,
            "loss_tangent": 0.02,
            "thickness_tolerance": 0.1
        }
    }

@pytest.fixture
def calculator(materials_data, tmp_path):
    """Returns a PCBDelayCalculator instance with a temporary materials file."""
    materials_file = tmp_path / "materials.json"
    with open(materials_file, 'w') as f:
        json.dump(materials_data, f)
    return PCBDelayCalculator(materials_file=str(materials_file))

# --- Unit Tests for Calculator Logic ---

def test_load_materials_error():
    """Test that FileNotFoundError is raised for a non-existent materials file."""
    with pytest.raises(FileNotFoundError):
        PCBDelayCalculator(materials_file="non_existent_file.json")

def test_calculate_effective_dielectric(calculator):
    """Test effective dielectric constant calculations."""
    # Microstrip
    er_eff_micro = calculator.calculate_effective_dielectric(4.0, 0.2, 0.035, 0.2, 'microstrip')
    assert math.isclose(er_eff_micro, 2.84, rel_tol=1e-2)
    # Stripline
    er_eff_strip = calculator.calculate_effective_dielectric(4.0, 0.2, 0.035, 0.2, 'stripline')
    assert er_eff_strip == 4.0

def test_estimate_delay_range(calculator):
    """Test the full delay range estimation."""
    result = calculator.estimate_delay_range(
        track_length_mm=50,
        pcb_type='test_material',
        trace_width=0.1,
        trace_thickness=0.035,
        dielectric_height=0.2,
        trace_type='microstrip'
    )
    assert 'min_delay_ns' in result
    assert 'max_delay_ns' in result
    assert 'nominal_delay_ns' in result
    assert math.isclose(result['nominal_delay_ns'], 0.275, rel_tol=1e-2)

def test_generate_sdc_constraints():
    """Test the SDC constraint generation function."""
    net_delays = {
        'data0': {'min_delay_ns': 0.1, 'max_delay_ns': 0.2, 'nominal_delay_ns': 0.15, 'er_eff_nominal': 3.5}
    }
    sdc = generate_sdc_constraints(net_delays, "test_clk")
    assert "set_input_delay -clock test_clk -min 0.100 [get_ports data0]" in sdc
    assert "set_input_delay -clock test_clk -max 0.200 [get_ports data0]" in sdc

# --- Integration Tests for CLI ---

@patch('sys.argv', [
    'PCBDelayCalc.py',
    '--nets', '{"data0": 50}',
    '--pcb-type', 'test_material',
    '--output-format', 'json'
])
def test_cli_json_output(capsys, calculator):
    """Test the CLI with JSON output format."""
    # Mock the calculator instance within the main function's scope
    with patch('PCBDelayCalc.PCBDelayCalculator', return_value=calculator):
        main()
        captured = capsys.readouterr()
        output_data = json.loads(captured.out)
        assert 'data0' in output_data
        assert 'nominal_delay_ns' in output_data['data0']
        assert math.isclose(output_data['data0']['nominal_delay_ns'], 0.275, rel_tol=1e-2)

@patch('sys.argv', [
    'PCBDelayCalc.py',
    '--nets', '{"data0": 50}',
    '--pcb-type', 'test_material',
    '--output-format', 'sdc'
])
def test_cli_sdc_output(capsys, calculator):
    """Test the CLI with SDC output format."""
    with patch('PCBDelayCalc.PCBDelayCalculator', return_value=calculator):
        main()
        captured = capsys.readouterr()
        assert "set_input_delay -clock sys_clk -min" in captured.out
        assert "set_input_delay -clock sys_clk -max" in captured.out

@patch('sys.argv', [
    'PCBDelayCalc.py',
    '--nets', '{"data0": 50}',
    '--pcb-type', 'non_existent_material'
])
def test_cli_invalid_pcb_type(caplog, calculator):
    """Test the CLI with an invalid PCB type."""
    with patch('PCBDelayCalc.PCBDelayCalculator', return_value=calculator):
        main()
        assert "PCB type 'non_existent_material' not found" in caplog.text

