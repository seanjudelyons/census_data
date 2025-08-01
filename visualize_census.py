#!/usr/bin/env python3
"""
Census Data Visualization Tool

This script provides tools to extract, analyze, and visualize historical Australian census data
from the downloaded HTML files.

Usage:
    python visualize_census.py [--state STATE] [--year YEAR] [--type TYPE]

Examples:
    python visualize_census.py                    # Interactive mode
    python visualize_census.py --state QLD        # Analyze Queensland data
    python visualize_census.py --year 1901        # Analyze 1901 census data
    python visualize_census.py --state NSW --year 1891  # Specific state and year
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configure visualization settings
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class CensusDataExtractor:
    """Extract and parse census data from HTML files"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "census_data_download"
        self.cache_file = self.base_path / "census_cache.json"
        self.data_cache = self.load_cache()
        
    def load_cache(self) -> dict:
        """Load cached data if available"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """Save extracted data to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.data_cache, f, indent=2)
    
    def find_census_files(self) -> List[Path]:
        """Find all census HTML files"""
        census_files = []
        
        # Search for census files in the directory structure
        for html_file in self.data_path.rglob("*.html"):
            if "census" in str(html_file).lower():
                census_files.append(html_file)
        
        return sorted(census_files)
    
    def parse_census_filename(self, filepath: Path) -> Dict[str, str]:
        """Extract metadata from census filename"""
        filename = filepath.name
        parts = filename.replace('.html', '').split('-')
        
        metadata = {
            'filepath': str(filepath),
            'filename': filename,
            'state': None,
            'year': None,
            'type': 'unknown'
        }
        
        # Extract state (usually first part)
        if len(parts) >= 2:
            metadata['state'] = parts[0]
        
        # Extract year (4-digit number)
        for part in parts:
            if re.match(r'^\d{4}$', part):
                metadata['year'] = part
                break
        
        # Determine if it's a collated or individual table
        if 'Collated_Census_Tables' in str(filepath):
            metadata['type'] = 'collated'
        elif 'Individual_Census_Tables' in str(filepath):
            metadata['type'] = 'individual'
        
        return metadata
    
    def extract_table_data(self, filepath: Path) -> List[Dict]:
        """Extract table data from census HTML file"""
        cache_key = str(filepath)
        
        # Check cache first
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        tables = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract all tables
            for table in soup.find_all('table'):
                table_data = self.parse_html_table(table)
                if table_data:
                    tables.append(table_data)
            
            # Cache the results
            self.data_cache[cache_key] = tables
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
        
        return tables
    
    def parse_html_table(self, table_element) -> Optional[Dict]:
        """Parse HTML table element into structured data"""
        data = {
            'caption': '',
            'headers': [],
            'rows': []
        }
        
        # Extract caption
        caption = table_element.find('caption')
        if caption:
            data['caption'] = caption.get_text(strip=True)
        
        # Extract headers
        thead = table_element.find('thead')
        if thead:
            header_rows = thead.find_all('tr')
            for row in header_rows:
                headers = [th.get_text(strip=True) for th in row.find_all(['th', 'td'])]
                data['headers'].append(headers)
        
        # Extract data rows
        tbody = table_element.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                data['rows'].append(cells)
        
        # Return None if no data found
        if not data['rows'] and not data['headers']:
            return None
        
        return data

class CensusVisualizer:
    """Visualize census data"""
    
    def __init__(self, extractor: CensusDataExtractor):
        self.extractor = extractor
        self.census_files = self.extractor.find_census_files()
        self.metadata = [self.extractor.parse_census_filename(f) for f in self.census_files]
        
    def get_overview_stats(self) -> Dict:
        """Get overview statistics of the census data"""
        stats = {
            'total_files': len(self.census_files),
            'states': Counter(),
            'years': Counter(),
            'types': Counter()
        }
        
        for meta in self.metadata:
            if meta['state']:
                stats['states'][meta['state']] += 1
            if meta['year']:
                stats['years'][meta['year']] += 1
            stats['types'][meta['type']] += 1
        
        return stats
    
    def plot_files_by_state(self):
        """Create bar chart of census files by state"""
        state_counts = Counter(m['state'] for m in self.metadata if m['state'])
        
        plt.figure(figsize=(10, 6))
        states = list(state_counts.keys())
        counts = list(state_counts.values())
        
        plt.bar(states, counts)
        plt.xlabel('State')
        plt.ylabel('Number of Census Files')
        plt.title('Distribution of Census Files by State')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return plt.gcf()
    
    def plot_files_by_year(self):
        """Create timeline of census files"""
        year_counts = Counter(m['year'] for m in self.metadata if m['year'])
        
        plt.figure(figsize=(12, 6))
        years = sorted(year_counts.keys())
        counts = [year_counts[y] for y in years]
        
        plt.plot(years, counts, marker='o', markersize=8, linewidth=2)
        plt.xlabel('Year')
        plt.ylabel('Number of Census Files')
        plt.title('Timeline of Census Data Collection')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()
    
    def analyze_population_data(self, state: Optional[str] = None, year: Optional[str] = None):
        """Analyze population data from census tables"""
        population_data = []
        
        # Filter files based on criteria
        filtered_files = []
        for i, meta in enumerate(self.metadata):
            if state and meta['state'] != state:
                continue
            if year and meta['year'] != year:
                continue
            filtered_files.append((self.census_files[i], meta))
        
        print(f"Analyzing {len(filtered_files)} census files...")
        
        # Extract population data
        for filepath, meta in tqdm(filtered_files[:10]):  # Limit to first 10 for demo
            tables = self.extractor.extract_table_data(filepath)
            
            for table in tables:
                # Look for population-related tables
                if any(keyword in str(table.get('caption', '')).lower() 
                      for keyword in ['population', 'total', 'persons', 'males', 'females']):
                    
                    population_data.append({
                        'state': meta['state'],
                        'year': meta['year'],
                        'caption': table.get('caption', ''),
                        'data': table
                    })
        
        return population_data
    
    def create_summary_report(self, output_file: str = "census_summary.txt"):
        """Create a summary report of the census data"""
        stats = self.get_overview_stats()
        
        report = []
        report.append("="*60)
        report.append("AUSTRALIAN HISTORICAL CENSUS DATA SUMMARY")
        report.append("="*60)
        report.append(f"\nTotal Census Files: {stats['total_files']}")
        
        report.append("\n\nFiles by State:")
        for state, count in sorted(stats['states'].items()):
            report.append(f"  {state}: {count} files")
        
        report.append("\n\nFiles by Year:")
        for year, count in sorted(stats['years'].items()):
            report.append(f"  {year}: {count} files")
        
        report.append("\n\nFiles by Type:")
        for ftype, count in stats['types'].items():
            report.append(f"  {ftype}: {count} files")
        
        report.append("\n\nYear Range:")
        years = [m['year'] for m in self.metadata if m['year']]
        if years:
            report.append(f"  Earliest: {min(years)}")
            report.append(f"  Latest: {max(years)}")
        
        report_text = '\n'.join(report)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        return report_text

def interactive_mode(visualizer: CensusVisualizer):
    """Interactive mode for exploring census data"""
    
    while True:
        print("\n" + "="*60)
        print("CENSUS DATA VISUALIZATION TOOL")
        print("="*60)
        print("\n1. Show overview statistics")
        print("2. Plot census files by state")
        print("3. Plot census files by year")
        print("4. Analyze population data")
        print("5. Create summary report")
        print("6. Extract specific table data")
        print("7. Save cache and exit")
        print("0. Exit without saving")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            stats = visualizer.get_overview_stats()
            print(f"\nTotal files: {stats['total_files']}")
            print("\nFiles by state:")
            for state, count in sorted(stats['states'].items()):
                print(f"  {state}: {count}")
            print("\nFiles by year:")
            for year, count in sorted(stats['years'].items()):
                print(f"  {year}: {count}")
                
        elif choice == '2':
            visualizer.plot_files_by_state()
            plt.show()
            
        elif choice == '3':
            visualizer.plot_files_by_year()
            plt.show()
            
        elif choice == '4':
            state = input("Enter state code (or press Enter for all): ").upper() or None
            year = input("Enter year (or press Enter for all): ") or None
            
            pop_data = visualizer.analyze_population_data(state, year)
            print(f"\nFound {len(pop_data)} population-related tables")
            
            if pop_data and input("\nShow first 5 table captions? (y/n): ").lower() == 'y':
                for i, data in enumerate(pop_data[:5]):
                    print(f"\n{i+1}. {data['caption']}")
                    
        elif choice == '5':
            report = visualizer.create_summary_report()
            print(report)
            print("\nReport saved to census_summary.txt")
            
        elif choice == '6':
            # List available states
            states = sorted(set(m['state'] for m in visualizer.metadata if m['state']))
            print("\nAvailable states:", ', '.join(states))
            state = input("Enter state code: ").upper()
            
            # List available years for that state
            years = sorted(set(m['year'] for m in visualizer.metadata 
                             if m['state'] == state and m['year']))
            print(f"\nAvailable years for {state}:", ', '.join(years))
            year = input("Enter year: ")
            
            # Find matching files
            matches = [(f, m) for f, m in zip(visualizer.census_files, visualizer.metadata)
                      if m['state'] == state and m['year'] == year]
            
            if matches:
                print(f"\nFound {len(matches)} files")
                for i, (f, m) in enumerate(matches[:5]):
                    print(f"{i+1}. {f.name}")
                    
                if input("\nExtract data from first file? (y/n): ").lower() == 'y':
                    tables = visualizer.extractor.extract_table_data(matches[0][0])
                    print(f"\nExtracted {len(tables)} tables")
                    
        elif choice == '7':
            visualizer.extractor.save_cache()
            print("Cache saved. Goodbye!")
            break
            
        elif choice == '0':
            print("Goodbye!")
            break

def main():
    parser = argparse.ArgumentParser(description='Visualize Australian historical census data')
    parser.add_argument('--state', help='Filter by state code (e.g., NSW, QLD)')
    parser.add_argument('--year', help='Filter by census year')
    parser.add_argument('--type', choices=['collated', 'individual'], 
                       help='Filter by table type')
    parser.add_argument('--report', action='store_true', 
                       help='Generate summary report only')
    
    args = parser.parse_args()
    
    # Initialize extractor and visualizer
    base_path = Path(__file__).parent
    extractor = CensusDataExtractor(base_path)
    visualizer = CensusVisualizer(extractor)
    
    if args.report:
        # Generate report only
        report = visualizer.create_summary_report()
        print(report)
    elif args.state or args.year or args.type:
        # Command-line mode with filters
        pop_data = visualizer.analyze_population_data(args.state, args.year)
        print(f"Found {len(pop_data)} population-related tables")
        
        # Create visualizations
        visualizer.plot_files_by_state()
        plt.savefig(f'census_by_state_{args.state or "all"}.png')
        
        visualizer.plot_files_by_year()
        plt.savefig(f'census_by_year_{args.year or "all"}.png')
        
        print("Visualizations saved to PNG files")
    else:
        # Interactive mode
        interactive_mode(visualizer)

if __name__ == "__main__":
    main()