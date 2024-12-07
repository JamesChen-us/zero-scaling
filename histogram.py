import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns
from datetime import datetime
from locustfile import create_function_mapping

def analyze_function_patterns(mapping_result):
    sorted_events = mapping_result['sorted_events']
    function_mapping = mapping_result['function_mapping']
    
    task_stats = defaultdict(lambda: {
        'durations': [],
        'requests_per_second': defaultdict(int),
        'total_calls': 0,
        'total_duration': 0
    })
    
    # Process per-task stats
    for app, func, start_time, end_time, duration in sorted_events:
        if (app, func) in function_mapping:
            task_name = function_mapping[(app, func)]
            duration_sec = float(duration)
            second = datetime.fromtimestamp(float(start_time)).replace(microsecond=0)
            
            stats = task_stats[task_name]
            stats['durations'].append(duration_sec)
            stats['requests_per_second'][second] += 1
            stats['total_calls'] += 1
            stats['total_duration'] += duration_sec
    
    if not task_stats:
        print("No mapped functions found in trace data")
        return None
    
    # Process overall request timeline
    overall_requests = defaultdict(int)
    for _, _, start_time, _, _ in sorted_events:
        second = datetime.fromtimestamp(float(start_time)).replace(microsecond=0)
        overall_requests[second] += 1
    
    sorted_times = sorted(overall_requests.items())
    timestamps = [t for t, _ in sorted_times]
    counts = [c for _, c in sorted_times]
    
    # Create figure with adjusted layout
    num_tasks = len(task_stats)
    total_rows = num_tasks + 1  # Add one row for the timeline
    fig = plt.figure(figsize=(15, 8 * total_rows))
    
    # Create timeline plot at the top
    ax_timeline = fig.add_subplot(total_rows, 1, 1)
    ax_timeline.plot(timestamps, counts, '-', linewidth=2)
    ax_timeline.set_title('Overall Requests per Second Over Time')
    ax_timeline.set_xlabel('Time')
    ax_timeline.set_ylabel('Number of Requests')
    plt.setp(ax_timeline.xaxis.get_majorticklabels(), rotation=45)
    
    # Create task-specific plots
    for idx, (task_name, stats) in enumerate(task_stats.items()):
        durations = stats['durations']
        requests = list(stats['requests_per_second'].values())
        
        # Adjust subplot positions to account for timeline
        ax1 = fig.add_subplot(total_rows, 2, 2*(idx + 1) + 1)
        create_duration_plot_on_axis(ax1, task_name, durations, stats)
        
        ax2 = fig.add_subplot(total_rows, 2, 2*(idx + 1) + 2)
        create_requests_plot_on_axis(ax2, task_name, requests)
    
    plt.tight_layout()
    return fig, {name: calc_task_metadata(stats) for name, stats in task_stats.items()}

def create_duration_plot_on_axis(ax, task_name, durations, stats):
    sns.histplot(durations, bins=30, kde=True, ax=ax)
    ax.set_title(f'Duration Distribution - {task_name}')
    ax.set_xlabel('Duration (seconds)')
    ax.set_ylabel('Frequency')
    
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
    if requests:
        sns.histplot(requests, bins=range(max(requests) + 2), ax=ax)
        ax.set_title(f'Requests per Second - {task_name}')
        ax.set_xlabel('Number of Requests')
        ax.set_ylabel('Frequency (Seconds)')
        
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
    ax.text(0.95, 0.95, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(facecolor='white', alpha=0.8))

def calc_task_metadata(stats):
    durations = stats['durations']
    return {
        'total_calls': stats['total_calls'],
        'total_duration': stats['total_duration'],
        'min_duration': min(durations) if durations else float('inf'),
        'max_duration': max(durations) if durations else 0
    }

def print_analysis_summary(task_metadata):
    """Print a detailed summary of the analysis"""
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

if __name__ == "__main__":
    # Example usage
    tasks = {
        'index': 1,
        'setCurrency': 2,
        'browseProduct': 10,
        'addToCart': 2,
        'viewCart': 3,
        'checkout': 1
    }
    
    mapping_result = create_function_mapping('/users/Jch270/zero-scaling/AzureFunctionsInvocationTrace.txt', tasks)
    fig, metadata = analyze_function_patterns(mapping_result)
    # fig = analyze_requests_over_time(mapping_result['sorted_events'])
    print_analysis_summary(metadata)
    
    # Save visualization
    plt.savefig('function_analysis.png', dpi=300, bbox_inches='tight')
    print("\nAnalysis visualization saved as 'function_analysis.png'")