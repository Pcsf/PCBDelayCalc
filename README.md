# PCB Delay Calculator

A Python-based CLI tool for estimating PCB track propagation delay, crucial for FPGA timing analysis. This tool considers track geometry, dielectric properties, and manufacturing tolerances to provide min/max delay analysis for use in FPGA `.sdc` files.

## Features

-   **Configurable Materials:** PCB material properties are loaded from `materials.json`, allowing for easy customization and addition of new materials.
-   **Command-Line Interface:** All parameters can be controlled via the CLI, making it suitable for scripting and interactive use.
-   **Flexible Output:** Supports multiple output formats, including human-readable text, JSON, and SDC constraints.
-   **Tolerance Analysis:** Accounts for variations in dielectric constant (`er`) and thickness to estimate a realistic delay range.

## Installation

No installation is required. The script is self-contained. Ensure you have Python 3 installed.

## Usage

The primary way to use the tool is through the command line.

```bash
python PCBDelayCalc.py --nets '{"data_bus_0": 25.4, "clock_line": 76.2}' --pcb-type fr4_standard
```

### CLI Arguments

| Argument              | Description                                                                              | Default          |
| --------------------- | ---------------------------------------------------------------------------------------- | ---------------- |
| `--nets`              | JSON string or file path defining net names and their lengths in mm. **(Required)**        | -                |
| `--pcb-type`          | The PCB material to use, as defined in `materials.json`.                                 | `fr4_standard`   |
| `--trace-width`       | The width of the trace in mm.                                                            | `0.1`            |
| `--trace-thickness`   | The thickness of the trace in mm.                                                        | `0.035`          |
| `--dielectric-height` | The height of the dielectric material in mm.                                             | `0.2`            |
| `--trace-type`        | The type of trace.                                                                       | `microstrip`     |
| `--clock-name`        | The name of the reference clock for SDC output.                                          | `sys_clk`        |
| `--output-format`     | The format for the output.                                                               | `human`          |

### Output Formats

-   **human:** A simple, human-readable summary.
-   **json:** Detailed results in JSON format, ideal for scripting.
-   **sdc:** Synopsys Design Constraints for direct use in FPGA timing analysis tools.

#### Example: JSON Output

```bash
python PCBDelayCalc.py --nets '{"data0": 50}' --output-format json
```

```json
{
    "data0": {
        "min_delay_ns": 0.259,
        "max_delay_ns": 0.303,
        "nominal_delay_ns": 0.279,
        "er_eff_nominal": 3.25,
        "er_eff_range": [
            3.0,
            3.5
        ],
        "velocity_mm_ps": 166.4
    }
}
```

## Customization

To add or modify PCB materials, edit the `materials.json` file. Each entry should define the material's relative permittivity (`er`), `er_tolerance`, and `thickness_tolerance`.

