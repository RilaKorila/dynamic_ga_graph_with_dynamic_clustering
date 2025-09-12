# Dynamic GA Graph with Dynamic Clustering

A multi-objective optimization system for generating layouts of dynamic graphs

## Overview

This project is a system that generates beautiful layouts by applying NSGA-II genetic algorithm-based multi-objective optimization to graphs that change over time.

### Key Features

- **Dynamic Graph Processing**: Processing of graph data that changes over time
- **Multi-objective Optimization**: Simultaneous optimization of 3 objective functions using NSGA-II
  - Sprawl (spread degree)
  - Clutter (node overlap penalty)
  - Time Smoothness (temporal smoothness)
- **Visualization**: Visualization of scatter plots, box plots, and hypervolume evolution
- **Baseline Comparison**: Comparative evaluation with SuperGraph method

## Project Structure

```
dynamic_ga_graph_with_dynamic_clustering/
├── java_dynamic_class/          # Java implementation (evaluation functions, graph processing)
│   └── ocha/itolab/koala/batch/py4j/
│       ├── nsga2.py            # NSGA-II implementation
│       ├── show_scatter_plot.py # Scatter plot generation
│       ├── calc_hypervolum.py   # Hypervolume calculation and visualization
│       └── data_process/        # Data processing modules
├── baseline/                    # Baseline methods
│   ├── baseline_motif.py       # SuperGraph method implementation
│   └── evaluate_baseline_motif.py # Baseline evaluation
├── data/                       # Datasets
│   ├── Cit-HepPh/             # Cit-HepPh dataset
│   └── NBAF_coauthors/        # NBAF coauthorship dataset
├── Koala-manygen/             # Java implementation (legacy)
└── _plot_result/             # Experimental results output
```

## Environment Setup

### 1. Configuration Files Setup

#### Python Constants File
Create `java_dynamic_class/ocha/itolab/koala/batch/py4j/constants.py`:

```python
JAR_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/test/share/py4j/py4j0.10.9.5.jar"
CLASS_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/java_dynamic_class"
PNG_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/_plot_result/"
SUPERGRAPH_PNG_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/_supergraph_result/"
NBAF_COAUTHORS_CSV_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/Koala-manygen/NBAF_Coauthorship_12dim.csv"
CIT_HEP_PH_DIR_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/data/Cit-HepPh/"
NBAF_COAUTHORS_DIR_PATH = "{PROJECT_ROOT}/dynamic_ga_graph_with_dynamic_clustering/data/NBAF_coauthors/"
```

#### Java Constants File
Create `Koala-manygen/src/ocha/itolab/koala/constants/Dataset.java`:

```java
package ocha.itolab.koala.constants;

public enum Dataset {
    CIT_HEP_PH(
            "{PROJECT_ROOT}/data/Cit-HepPh/",
            "{PROJECT_ROOT}/data/Cit-HepPh/filtered_coms/",
            "Cit-HepPh"),
    NBAF_COAUTHORS(
            "{PROJECT_ROOT}/data/NBAF_coauthors/",
            "{PROJECT_ROOT}/data/NBAF_coauthors/filtered_coms/",
            "NBAF_coauthors");

    private String dataDirPath;
    private String comsPath;
    private String name;

    Dataset(final String dataDirPath, final String comsPath, final String name) {
        this.dataDirPath = dataDirPath;
        this.comsPath = comsPath;
        this.name = name;
    }

    public String getDataDirPath() { return this.dataDirPath; }
    public String getComsPath() { return this.comsPath; }
    public String getName() { return this.name; }
}
```

Replace `{PROJECT_ROOT}` with the absolute path to your project root directory.

### 2. Java Environment Setup

```bash
# Compile Java files
sh compile_java.sh  # For Windows, change colons to semicolons in compile_java.sh
```

### 3. Python Environment Setup

```bash
# Create and activate virtual environment
python -m venv env
source env/bin/activate  # Linux/Mac
# env\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Running Main Experiments

```bash
# Execute multi-objective optimization for dynamic graphs
sh run.sh
```

### 2. Result Visualization

#### Scatter Plot Generation
```bash
sh show_fitness_scatters.sh
```

#### Hypervolume Evolution Visualization
```bash
python java_dynamic_class/ocha/itolab/koala/batch/py4j/calc_hypervolum.py
```

#### Baseline Comparison (Box Plots)
```bash
python baseline/evaluate_baseline_motif.py
```

### 3. Layout HTML Output

```bash
# Convert CSV files to HTML
sh export_as_html.sh
```

## Main Components

### NSGA-II Implementation (`nsga2.py`)

- **Multi-objective Optimization**: Simultaneous optimization of 3 objective functions
- **Genetic Operations**: Implementation of crossover, mutation, and selection
- **Dynamic Layout**: Maintaining temporal continuity using previous timestamp layout information

### Evaluation Functions

1. **Sprawl**: Graph spread degree (lower is better)
2. **Clutter**: Node overlap penalty (lower is better)
3. **Time Smoothness**: Temporal smoothness (lower is better)

### Visualization Tools

- **Scatter Plots**: Visualization of relationships between objective functions
- **Box Plots**: Comparative evaluation of multiple methods
- **Hypervolume**: Tracking evolution of multi-objective optimization

## Experimental Settings

### Parameters

- **Population Size**: 20
- **Generations**: 40
- **Crossover Rate**: 0.9
- **Coordinate Range**: -10.0 to 10.0

### Datasets

- **Cit-HepPh**: Physics paper citation network
- **NBAF_coauthors**: Coauthorship network

## Output Files

- `_csv_result/`: Experimental results (layout CSV)
- `_plot_result/`: Experimental results (PNG, various statistics)
- `_supergraph_result/`: SuperGraph method results
- `boxplots_out/`: Box plots

## Troubleshooting

### Hypervolume Zero Problem

- **Cause**: Inappropriate reference point setting
- **Solution**: Set `self.ref_hv` to fixed values in `nsga2.py`

### Python Dependency Errors

```bash
# Individual installation
pip install deap py4j numpy matplotlib pandas networkx
```

## Technical Details

### Genetic Operations

- **Crossover**: `tools.cxSimulatedBinaryBounded` - NSGA-II compliant real-valued crossover ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/crossover.html#cxSimulatedBinaryBounded))
- **Mutation**: `tools.mutPolynomialBounded` - Polynomial mutation ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/mutation.html#mutPolynomialBounded))
- **Selection**: `tools.selNSGA2` - NSGA-II non-dominated sorting selection ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/emo.html#selNSGA2))

### Evaluation Function Implementation

- **Java Implementation**: Fast graph processing and evaluation computation
- **Python Integration**: Java-Python integration via Py4J

### Data Formats

- **Input**: TSV format edge lists
- **Output**: CSV format coordinate data
- **Visualization**: PNG, HTML formats

## References

- [DEAP Library](https://dse-souken.com/2021/05/25/ai-19/)
- [Py4J - Java Python Integration](https://qiita.com/riverwell/items/e90cbbfdac439e6e9d30)
- [NSGA-II Algorithm](https://ieeexplore.ieee.org/document/996017)
