# Census Data Visualization Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the visualization tool:**
   ```bash
   python visualize_census.py
   ```

## Features

### Interactive Mode
The default mode provides an interactive menu with these options:
- View overview statistics (file counts by state/year)
- Generate charts showing distribution of census files
- Analyze population data from tables
- Create summary reports
- Extract specific table data

### Command Line Mode
```bash
# Generate report only
python visualize_census.py --report

# Analyze specific state
python visualize_census.py --state QLD

# Analyze specific year
python visualize_census.py --year 1901

# Combine filters
python visualize_census.py --state NSW --year 1891
```

## What the Tool Does

### Data Extraction
- Parses HTML census files to extract table data
- Identifies metadata (state, year, table type) from filenames
- Caches extracted data for faster subsequent runs

### Visualizations
1. **Files by State**: Bar chart showing census file distribution across states
2. **Files by Year**: Timeline showing when census data was collected
3. **Population Analysis**: Extracts and analyzes population-related tables

### Reports
Generates comprehensive summary reports including:
- Total file counts
- Distribution by state and year
- Date range of census data
- File type breakdown (collated vs individual tables)

## Understanding the Data

The census files contain various types of information:
- **Collated Tables**: Summary data for entire states/regions
- **Individual Tables**: Detailed breakdowns by district, age, occupation, etc.

Common table types include:
- Population by age and gender
- Occupational statistics
- Religious affiliations
- Education levels
- Birthplace/nationality data

## Tips for Analysis

1. Start with the overview statistics to understand data coverage
2. Use the interactive mode to explore before running specific analyses
3. The cache file (`census_cache.json`) speeds up repeated analyses
4. Collated tables are good for high-level summaries
5. Individual tables provide more granular demographic data

## Output Files

- `census_summary.txt`: Text summary of all census data
- `census_by_state_*.png`: Visualization of files by state
- `census_by_year_*.png`: Timeline visualization
- `census_cache.json`: Cached extracted data