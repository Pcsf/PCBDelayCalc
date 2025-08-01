import math
import json
import argparse
import logging
import os
from typing import Dict, Any, Tuple, List

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
C0 = 2.998e8  # Speed of light in vacuum (m/s)

class PCBDelayCalculator:
    """
    Calculates PCB track group delay considering manufacturing tolerances.
    """

    def __init__(self, materials_file: str = 'materials.json'):
        """
        Initializes the calculator and loads PCB material properties.
        
        Args:
            materials_file: Path to the JSON file with material properties.
        """
        self.pcb_params = self._load_materials(materials_file)
        logging.info(f"Loaded {len(self.pcb_params)} materials from {materials_file}")

    def _load_materials(self, materials_file: str) -> Dict[str, Any]:
        """Loads material properties from a JSON file."""
        try:
            with open(materials_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Material file not found: {materials_file}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {materials_file}")
            raise

    def calculate_effective_dielectric(
        self, er: float, trace_width: float, trace_thickness: float,
        dielectric_height: float, trace_type: str = 'microstrip'
    ) -> float:
        """
        Calculates effective dielectric constant (er_eff) using approximation formulas.
        """
        w_h = trace_width / dielectric_height
        t_h = trace_thickness / dielectric_height

        if trace_type == 'microstrip':
            if w_h >= 1:
                er_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / w_h)**(-0.5)
            else:
                er_eff = (er + 1) / 2 + (er - 1) / 2 * ((1 + 12 / w_h)**(-0.5) + 0.04 * (1 - w_h)**2)
            
            # Thickness correction
            er_eff -= (er_eff - 1) * t_h / (4.6 * math.sqrt(w_h))
        elif trace_type == 'stripline':
            er_eff = er
        else:
            raise ValueError("trace_type must be 'microstrip' or 'stripline'")
        
        return er_eff

    def calculate_propagation_velocity(self, er_eff: float) -> float:
        """Calculates propagation velocity from effective dielectric constant."""
        return C0 / math.sqrt(er_eff)

    def calculate_group_delay(self, track_length_mm: float, er_eff: float) -> float:
        """Calculates group delay for a given track length and er_eff."""
        track_length_m = track_length_mm / 1000.0
        velocity = self.calculate_propagation_velocity(er_eff)
        return track_length_m / velocity

    def estimate_delay_range(
        self, track_length_mm: float, pcb_type: str, trace_width: float,
        trace_thickness: float, dielectric_height: float, trace_type: str,
        additional_tolerance: float = 0.05
    ) -> Dict[str, Any]:
        """
        Estimates min/max delay range considering manufacturing tolerances.
        
        This method calculates the nominal, minimum, and maximum propagation delays
        for a PCB trace based on its physical dimensions, the PCB material properties,
        and manufacturing tolerances. It accounts for variations in dielectric constant
        (er) and dielectric height due to thickness tolerances.
        
        Args:
            track_length_mm: The length of the trace in millimeters.
            pcb_type: The type of PCB material (must match a key in materials.json).
            trace_width: The width of the trace in millimeters.
            trace_thickness: The thickness of the trace in millimeters.
            dielectric_height: The height of the dielectric material in millimeters.
            trace_type: The type of trace ('microstrip' or 'stripline').
            additional_tolerance: An additional safety margin factor (default 0.05 or 5%).
            
        Returns:
            A dictionary containing:
                - 'min_delay_ns': Minimum estimated delay in nanoseconds.
                - 'max_delay_ns': Maximum estimated delay in nanoseconds.
                - 'nominal_delay_ns': Nominal estimated delay in nanoseconds.
                - 'er_eff_nominal': Nominal effective dielectric constant.
                - 'er_eff_range': Tuple of (min, max) effective dielectric constants.
                - 'velocity_mm_ps': Nominal propagation velocity in millimeters per picosecond.
        """
        if pcb_type not in self.pcb_params:
            raise ValueError(f"PCB type '{pcb_type}' not found in materials file.")
        
        params = self.pcb_params[pcb_type]
        er_nominal = params['er']
        
        # Calculate nominal effective dielectric
        er_eff_nominal = self.calculate_effective_dielectric(
            er_nominal, trace_width, trace_thickness, dielectric_height, trace_type)
        
        # Calculate min/max considering tolerances
        er_min = er_nominal - params['er_tolerance']
        er_max = er_nominal + params['er_tolerance']
        
        thickness_var = params['thickness_tolerance']
        dielectric_height_min = dielectric_height * (1 - thickness_var)
        dielectric_height_max = dielectric_height * (1 + thickness_var)
        
        er_eff_min = self.calculate_effective_dielectric(
            er_min, trace_width, trace_thickness, dielectric_height_max, trace_type)
        er_eff_max = self.calculate_effective_dielectric(
            er_max, trace_width, trace_thickness, dielectric_height_min, trace_type)
        
        # Calculate delays
        delay_nominal = self.calculate_group_delay(track_length_mm, er_eff_nominal)
        delay_min = self.calculate_group_delay(track_length_mm, er_eff_max) # Min delay from max er_eff
        delay_max = self.calculate_group_delay(track_length_mm, er_eff_min) # Max delay from min er_eff
        
        # Apply additional safety margin
        delay_min_final = delay_min * (1 - additional_tolerance)
        delay_max_final = delay_max * (1 + additional_tolerance)
        
        return {
            'min_delay_ns': delay_min_final * 1e9,
            'max_delay_ns': delay_max_final * 1e9,
            'nominal_delay_ns': delay_nominal * 1e9,
            'er_eff_nominal': er_eff_nominal,
            'er_eff_range': (er_eff_min, er_eff_max),
            'velocity_mm_ps': self.calculate_propagation_velocity(er_eff_nominal) / 1e3 # m/s to mm/ps
        }

def generate_sdc_constraints(net_delays: Dict[str, Dict[str, Any]], clock_name: str) -> str:
    """
    Generates SDC constraint strings from delay results.
    
    Args:
        net_delays: A dictionary mapping net names to their delay analysis results.
        clock_name: The name of the reference clock for the SDC constraints.
        
    Returns:
        A string containing the formatted SDC constraints.
    """
    lines = [f"# PCB Track Delay Constraints for clock: {clock_name}"]
    for net_name, delays in net_delays.items():
        lines.extend([
            f"# Net: {net_name}",
            f"# Nominal delay: {delays['nominal_delay_ns']:.3f} ns, Effective Er: {delays['er_eff_nominal']:.2f}",
            f"set_input_delay -clock {clock_name} -min {delays['min_delay_ns']:.3f} [get_ports {net_name}]",
            f"set_input_delay -clock {clock_name} -max {delays['max_delay_ns']:.3f} [get_ports {net_name}]",
            ""
        ])
    return "\n".join(lines)

def main():
    """Main function to run the CLI."""
    parser = argparse.ArgumentParser(description="PCB Delay Calculator for FPGA Timing Analysis")
    
    parser.add_argument("--nets", type=str, required=True, help='JSON string, CSV file path, or JSON file path for nets. Ex: \'{"net1": 25.4, "net2": 50.8}\' or nets.json or nets.csv')
    parser.add_argument("--pcb-type", type=str, default='fr4_standard', help="PCB material type (e.g., 'fr4_standard')")
    parser.add_argument("--trace-width", type=float, default=0.1, help="Trace width in mm")
    parser.add_argument("--trace-thickness", type=float, default=0.035, help="Trace thickness in mm (1oz copper)")
    parser.add_argument("--dielectric-height", type=float, default=0.2, help="Dielectric height in mm")
    parser.add_argument("--trace-type", type=str, default='microstrip', choices=['microstrip', 'stripline'], help="Trace type")
    parser.add_argument("--clock-name", type=str, default='sys_clk', help="Reference clock name for SDC constraints")
    parser.add_argument("--output-format", type=str, default='human', choices=['human', 'json', 'sdc'], help="Output format")
    parser.add_argument("--list-materials", action='store_true', help="List all available materials from materials.json")
    
    args = parser.parse_args()
    
    calc = PCBDelayCalculator()
    
    if args.list_materials:
        print("Available PCB Materials:")
        for material in calc.pcb_params.keys():
            print(f"  - {material}")
        return
    
    try:
        # Load nets from JSON string, JSON file, or CSV file
        if os.path.exists(args.nets):
            if args.nets.endswith('.csv'):
                import csv
                track_lengths = {}
                with open(args.nets, 'r') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if len(row) == 2:
                            try:
                                track_lengths[row[0]] = float(row[1])
                            except ValueError:
                                logging.warning(f"Skipping invalid CSV row: {row}")
            else:
                with open(args.nets, 'r') as f:
                    track_lengths = json.load(f)
        else:
            track_lengths = json.loads(args.nets)
    except (json.JSONDecodeError, FileNotFoundError, csv.Error) as e:
        logging.error(f"Invalid nets format. Must be a valid JSON string, JSON file, or CSV file. Error: {e}")
        return

    calc = PCBDelayCalculator()
    net_delays = {}
    
    for net_name, length in track_lengths.items():
        try:
            result = calc.estimate_delay_range(
                track_length_mm=length,
                pcb_type=args.pcb_type,
                trace_width=args.trace_width,
                trace_thickness=args.trace_thickness,
                dielectric_height=args.dielectric_height,
                trace_type=args.trace_type
            )
            net_delays[net_name] = result
        except ValueError as e:
            logging.error(f"Error processing net {net_name}: {e}")
            return
            
    if args.output_format == 'human':
        for net, delays in net_delays.items():
            logging.info(
                f"{net:15} ({track_lengths[net]:5.1f}mm): "
                f"{delays['min_delay_ns']:.3f} - {delays['max_delay_ns']:.3f} ns "
                f"(nom: {delays['nominal_delay_ns']:.3f} ns)"
            )
    elif args.output_format == 'sdc':
        print(generate_sdc_constraints(net_delays, args.clock_name))
    elif args.output_format == 'json':
        print(json.dumps(net_delays, indent=4))

if __name__ == "__main__":
    main()
