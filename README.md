# PCB Delay Calculator

A Python-based CLI tool for estimating PCB track propagation delay, crucial for FPGA timing analysis. This tool considers track geometry, dielectric properties, and manufacturing tolerances to provide min/max delay analysis for use in FPGA `.sdc` timing constraint files.

## Features

-   **Configurable Materials:** PCB material properties are loaded from `materials.json`, allowing for easy customization and addition of new materials.
-   **Flexible Net Input:** Accepts netlists from a JSON string, a JSON file, or a CSV file.
-   **Command-Line Interface:** All parameters can be controlled via the CLI, making it suitable for scripting and interactive use.
-   **Multiple Output Formats:** Supports human-readable text, JSON for scripting, and SDC (Synopsys Design Constraints) for direct use in FPGA tools.
-   **Tolerance Analysis:** Accounts for variations in dielectric constant (`er`) and board thickness to estimate a realistic delay range.
-   **Trace Types:** Supports both `microstrip` and `stripline` trace geometries.

## Installation

No external libraries are required. The script is self-contained and runs with a standard Python 3 installation.

## Usage

The primary way to use the tool is through the command line. All parameters are configurable via arguments.

### CLI Arguments

| Argument | Description | Choices | Default |
| --- | --- | --- | --- |
| `--nets` | JSON string, JSON file, or CSV file defining net names and their lengths in mm. **(Required)** | | - |
| `--pcb-type` | The PCB material to use, as defined in `materials.json`. | | `fr4_standard` |
| `--trace-width` | The width of the trace in mm. | | `0.1` |
| `--trace-thickness` | The thickness of the trace in mm (1oz copper is ~0.035mm). | | `0.035` |
| `--dielectric-height` | The height of the dielectric material in mm. | | `0.2` |
| `--trace-type` | The type of trace geometry. | `microstrip`, `stripline` | `microstrip` |
| `--clock-name` | The name of the reference clock for SDC output. | | `sys_clk` |
| `--output-format` | The format for the output. | `human`, `json`, `sdc` | `human` |
| `--list-materials` | List all available materials from `materials.json` and exit. | | `False` |

### Examples

#### 1. Basic Calculation with a JSON String

Provide a simple JSON string directly on the command line for quick calculations.

```bash
python PCBDelayCalc.py --nets '{"data_bus_0": 25.4, "clock_line": 76.2}' --pcb-type fr4_standard
```

#### 2. Using a CSV File for Net Input

For larger netlists, you can use a CSV file with `net_name,length_mm` format.

**`nets.csv`:**
```csv
data0,50.5
data1,52.1
addr0,100.0
```

**Command:**
```bash
python PCBDelayCalc.py --nets nets.csv --output-format human
```

#### 3. Generating SDC Constraints from a JSON File

Use a JSON file for nets and output the results as SDC constraints for your FPGA project.

**`nets.json`:**
```json
{
  "spi_clk": 45.0,
  "spi_mosi": 48.2,
  "spi_miso": 47.5
}
```

**Command:**
```bash
python PCBDelayCalc.py --nets nets.json --pcb-type rogers_4350b --clock-name "fpga_clk" --output-format sdc
```

**Output:**
```sdc
# PCB Track Delay Constraints for clock: fpga_clk
# Net: spi_clk
# Nominal delay: 0.241 ns, Effective Er: 2.88
set_input_delay -clock fpga_clk -min 0.228 [get_ports spi_clk]
set_input_delay -clock fpga_clk -max 0.255 [get_ports spi_clk]

# Net: spi_mosi
# Nominal delay: 0.258 ns, Effective Er: 2.88
set_input_delay -clock fpga_clk -min 0.244 [get_ports spi_mosi]
set_input_delay -clock fpga_clk -max 0.273 [get_ports spi_mosi]

# Net: spi_miso
# Nominal delay: 0.254 ns, Effective Er: 2.88
set_input_delay -clock fpga_clk -min 0.241 [get_ports spi_miso]
set_input_delay -clock fpga_clk -max 0.269 [get_ports spi_miso]
```

#### 4. Listing Available Materials

Check which materials are defined in your `materials.json` file.

```bash
python PCBDelayCalc.py --list-materials
```

**Output:**
```
Available PCB Materials:
  - fr4_standard
  - rogers_4003c
  - rogers_4350b
  - polyimide_flex
```

#### 5. Getting Detailed JSON Output

For scripting or further analysis, the JSON output provides all calculated values.

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
            2.98,
            3.51
        ],
        "velocity_mm_ps": 166.4
    }
}
```

## Customization

To add or modify PCB materials, edit the `materials.json` file. Each entry must define the material's relative permittivity (`er`), its tolerance (`er_tolerance`), and the board's manufacturing thickness tolerance (`thickness_tolerance`).

