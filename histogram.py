# Function Analysis and Visualization Script
# This script analyzes function execution patterns from Azure function traces 
# and creates visualizations for workload analysis

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns
from datetime import datetime
from locustfile import create_function_mapping

def analyze_function_patterns(mapping_result):
    """
    Analyzes patterns in function execution data and generates visualizations
    
    Args:
        mapping_result: Dictionary containing sorted events and function mappings
        
    Returns:
        tuple: (matplotlib figure, metadata dictionary)
    """
    sorted_events = mapping_result['sorted_events']
    function_mapping = mapping_result['function_mapping']
    
    # Initialize statistics tracking for each task
    task_stats = defaultdict(lambda: {
        'durations': [],              # List of execution durations
        'requests_per_second': defaultdict(int),  # Request count per second
        'total_calls': 0,             # Total number of function calls
        'total_duration': 0           # Total execution time
    })
    
    # Process each event and collect statistics
    for app, func, start_time, end_time, duration in sorted_events:
        if (app, func) in function_mapping:
            task_name = function_mapping[(app, func)]
            duration_sec = float(duration)
            # Round timestamp to nearest second for grouping
            second = datetime.fromtimestamp(float(start_time)).replace(microsecond=0)
            
            # Update statistics for this task
            stats = task_stats[task_name]
            stats['durations'].append(duration_sec)
            stats['requests_per_second'][second] += 1
            stats['total_calls'] += 1
            stats['total_duration'] += duration_sec
    
    if not task_stats:
        print("No mapped functions found in trace data")
        return None
    
    # Calculate overall request timeline
    overall_requests = defaultdict(int)
    for _, _, start_time, _, _ in sorted_events:
        second = datetime.fromtimestamp(float(start_time)).replace(microsecond=0)
        overall_requests[second] += 1
    
    # Prepare timeline data
    sorted_times = sorted(overall_requests.items())
    timestamps = [t for t, _ in sorted_times]
    counts = [c for _, c in sorted_times]
    
    # Setup visualization layout
    num_tasks = len(task_stats)
    total_rows = num_tasks + 1  # Add row for timeline
    fig = plt.figure(figsize=(15, 8 * total_rows))
    
    # Create main timeline plot
    ax_timeline = fig.add_subplot(total_rows, 1, 1)
    ax_timeline.plot(timestamps, counts, '-', linewidth=2)
    ax_timeline.set_title('Overall Requests per Second Over Time')
    ax_timeline.set_xlabel('Time')
    ax_timeline.set_ylabel('Number of Requests')
    plt.setp(ax_timeline.xaxis.get_majorticklabels(), rotation=45)
    
    # Create individual plots for each task
    for idx, (task_name, stats) in enumerate(task_stats.items()):
        durations = stats['durations']
        requests = list(stats['requests_per_second'].values())
        
        # Create duration distribution plot
        ax1 = fig.add_subplot(total_rows, 2, 2*(idx + 1) + 1)
        create_duration_plot_on_axis(ax1, task_name, durations, stats)
        
        # Create requests per second distribution plot
        ax2 = fig.add_subplot(total_rows, 2, 2*(idx + 1) + 2)
        create_requests_plot_on_axis(ax2, task_name, requests)
    
    plt.tight_layout()
    return fig, {name: calc_task_metadata(stats) for name, stats in task_stats.items()}

def create_duration_plot_on_axis(ax, task_name, durations, stats):
    """
    Creates a histogram of function execution durations
    
    Args:
        ax: matplotlib axis object
        task_name: Name of the task
        durations: List of execution durations
        stats: Dictionary containing task statistics
    """
    sns.histplot(durations, bins=30, kde=True, ax=ax)
    ax.set_title(f'Duration Distribution - {task_name}')
    ax.set_xlabel('Duration (seconds)')
    ax.set_ylabel('Frequency')
    
    # Add statistics text box
    stats_text = (
        f"Statistics:\n"
        f"Mean: {np.mean(durations):.2f}s\n"
        f"Median: {np.median(durations):.2f}s\n"
        f"95th percentile: {np.percentile(durations, 95):.2f}s\n"
        f"Total calls: {stats['total_calls']}\n"
        f"Total duration: {stats['total_duration']:.2f}s"
    )
    add_stats_box(ax, stats_text)

def create_requests_plot_on_axis(ax, task_name, requests):
    """
    Creates a histogram of requests per second
    
    Args:
        ax: matplotlib axis object
        task_name: Name of the task
        requests: List of request counts per second
    """
    if requests:
        sns.histplot(requests, bins=range(max(requests) + 2), ax=ax)
        ax.set_title(f'Requests per Second - {task_name}')
        ax.set_xlabel('Number of Requests')
        ax.set_ylabel('Frequency (Seconds)')
        
        # Add statistics text box
        request_stats = (
            f"Request Stats:\n"
            f"Mean: {np.mean(requests):.2f}\n"
            f"Max: {max(requests)}\n"
            f"Total seconds: {len(requests)}"
        )
        add_stats_box(ax, request_stats)
    else:
        ax.text(0.5, 0.5, 'No request data available', ha='center', va='center')

def add_stats_box(ax, stats_text):
    """Adds a text box with statistics to the plot"""
    ax.text(0.95, 0.95, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(facecolor='white', alpha=0.8))

def calc_task_metadata(stats):
    """
    Calculates metadata for a task from its statistics
    
    Args:
        stats: Dictionary containing task statistics
        
    Returns:
        dict: Metadata including call counts and duration statistics
    """
    durations = stats['durations']
    return {
        'total_calls': stats['total_calls'],
        'total_duration': stats['total_duration'],
        'min_duration': min(durations) if durations else float('inf'),
        'max_duration': max(durations) if durations else 0
    }

def print_analysis_summary(task_metadata):
    """
    Prints a formatted summary of the analysis results
    
    Args:
        task_metadata: Dictionary containing task statistics
    """
    print("\nFunction Analysis Summary:")
    print("-" * 80)
    
    for task_name, meta in task_metadata.items():
        print(f"\nTask: {task_name}")
        print(f"Total Invocations: {meta['total_calls']}")
        print(f"Total Duration: {meta['total_duration']:.2f}s")
        print(f"Average Duration: {meta['total_duration']/meta['total_calls']:.2f}s")
        print(f"Min Duration: {meta['min_duration']:.2f}s")
        print(f"Max Duration: {meta['max_duration']:.2f}s")
        print("-" * 40)

# Main execution block
if __name__ == "__main__":
    # Define task weights for function mapping
    tasks = {
        'index': 1,
        'setCurrency': 2,
        'browseProduct': 10,
        'addToCart': 2,
        'viewCart': 3,
        'checkout': 1
    }
    
    # Process trace file and create visualizations
    mapping_result = create_function_mapping('/users/Jch270/zero-scaling/AzureFunctionsInvocationTrace.txt', tasks)
    fig, metadata = analyze_function_patterns(mapping_result)
    print_analysis_summary(metadata)
    plt.savefig('function_analysis.png', dpi=300, bbox_inches='tight')
    print("\nAnalysis visualization saved as 'function_analysis.png'")