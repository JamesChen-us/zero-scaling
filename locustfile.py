#!/usr/bin/python

# Import required libraries for load testing and data processing
import time
from collections import defaultdict
import random
from locust import HttpUser, TaskSet, between, events, task

def create_function_mapping(trace_file_path, desired_tasks):
    """
    Creates a mapping between Azure Functions and desired task types based on trace data.
    
    Args:
        trace_file_path (str): Path to the Azure Functions trace file
        desired_tasks (dict): Dictionary mapping task names to their desired weights
        
    Returns:
        dict: Contains sorted events and function mappings
    """
    func_counts = {}
    trace_events = []
    
    # Read trace file and collect events within first 4000 seconds
    with open(trace_file_path, 'r') as f:
        next(f)  # Skip header line
        for line in f:
            app, func, end_timestamp, duration = line.strip().split(',')
            end_time = float(end_timestamp)
            duration = float(duration)
            start_time = end_time - duration
            
            if end_time <= 4000:  # Only consider events in first 4000 seconds
                func_counts[func] = func_counts.get(func, 0) + 1
                trace_events.append((app, func, start_time, end_time, duration))
    
    sorted_events = sorted(trace_events, key=lambda x: x[2])
    
    # Sort functions by their frequency in descending order
    sorted_funcs = sorted(
        [(func, count) for func, count in func_counts.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    # Calculate weights and targets
    total_weight = sum(desired_tasks.values())
    total_function_count = sum(func_counts.values())
    task_targets = {
        task: (weight / total_weight) * total_function_count 
        for task, weight in desired_tasks.items()
    }
    
    # Initialize mapping data structures
    function_mapping = {}
    task_current_counts = defaultdict(int)
    unassigned_funcs = sorted_funcs.copy()
    
    # First pass: Ensure minimum representation for each task
    min_target_ratio = 0.3  # At least 30% of target for each task
    for task, target in task_targets.items():
        min_required = target * min_target_ratio
        
        while task_current_counts[task] < min_required and unassigned_funcs:
            # Find smallest function that won't exceed target by more than 20%
            best_func_idx = -1
            for i, (func, count) in enumerate(unassigned_funcs):
                if task_current_counts[task] + count <= target * 1.2:
                    best_func_idx = i
                    break
            
            if best_func_idx == -1:
                break
                
            # Assign function to task
            func, count = unassigned_funcs.pop(best_func_idx)
            for app, f, _, _, _ in trace_events:
                if f == func:
                    function_mapping[(app, f)] = task
            task_current_counts[task] += count
    
    # Second pass: Distribute remaining functions to minimize deviation
    while unassigned_funcs:
        func, count = unassigned_funcs.pop(0)
        
        # Find task that minimizes maximum deviation
        best_task = None
        min_max_deviation = float('inf')
        
        for task in task_targets:
            temp_counts = task_current_counts.copy()
            temp_counts[task] += count
            
            max_deviation = max(
                abs(temp_counts[t] / task_targets[t] - 1)
                for t in task_targets
            )
            
            if max_deviation < min_max_deviation:
                min_max_deviation = max_deviation
                best_task = task
        
        # Assign to best task
        for app, f, _, _, _ in trace_events:
            if f == func:
                function_mapping[(app, f)] = best_task
        task_current_counts[best_task] += count
    
    # Print mapping analysis
    print("\nMapping Analysis:")
    final_counts = defaultdict(int)
    for app, func, _, _, _ in sorted_events:
        if (app, func) in function_mapping:
            task = function_mapping[(app, func)]
            final_counts[task] += 1
    
    for task, target in task_targets.items():
        actual = final_counts[task]
        deviation = (actual - target) / target * 100 if target > 0 else float('inf')
        print(f"\n{task}:")
        print(f"Actual calls: {actual}")
        print(f"Expected: {target:.2f}")
        print(f"Deviation: {deviation:.1f}%")
        print(f"Target weight: {desired_tasks[task]}/{total_weight}")

    return {
        'sorted_events': sorted_events,
        'function_mapping': function_mapping
    }

# Sample product IDs for the e-commerce simulation
products = [
    '0PUK6V6EV0', '1YMWWN1N4O', '2ZYFJ3GM2N', '66VCHSJNUP',
    '6E92ZMYYFZ', '9SIQT8TOJO', 'L9ECAV7KIM', 'LS4PSXUNUM', 'OLJCESPC7Z'
]

# Task weights for distribution
tasks = {
    'index': 1,
    'setCurrency': 2,
    'browseProduct': 10,
    'addToCart': 2,
    'viewCart': 3,
    'checkout': 1
}

# Create initial function mapping
mapping_result = create_function_mapping('/users/Jch270/zero-scaling/AzureFunctionsInvocationTrace.txt', tasks)

class TraceReplayTaskSet(TaskSet):
    """
    TaskSet that replays function traces according to the original timing
    Each user follows the exact timing from the trace data
    """
    
    # Shared class-level variables
    trace_data = None
    function_mapping = None
    global_start_time = None
    
    @classmethod
    def setup_trace_data(cls):
        """Initialize trace data if not already loaded"""
        if cls.trace_data is None:
            cls.trace_data = mapping_result['sorted_events']
            cls.function_mapping = mapping_result['function_mapping']
            cls.global_start_time = time.time()
            cls.url = "http://IP:PORT"
            cls.host = "kn-frontend.default.127.0.0.1.sslip.io"
    
    def on_start(self):
        """Initialize user session"""
        self.setup_trace_data()
        self.current_idx = 0
    
    # Task definitions for different e-commerce operations
    def index(l):
        """Simulate homepage visit"""
        l.client.get(l.url + "/", headers={"host": l.host})

    def setCurrency(l):
        """Simulate currency selection"""
        currencies = ['EUR', 'USD', 'JPY', 'CAD']
        l.client.post(l.url + "/setCurrency",
            {'currency_code': random.choice(currencies)}, headers={"host": l.host})

    def browseProduct(l):
        """Simulate product browsing"""
        l.client.get(l.url + "/product/" + random.choice(products), headers={"host": l.host})

    def viewCart(l):
        """Simulate cart view"""
        l.client.get(l.url + "/cart", headers={"host": l.host})

    def addToCart(l):
        """Simulate adding product to cart"""
        product = random.choice(products)
        l.client.get(l.url + "/product/" + product, headers={"host": l.host})
        l.client.post(l.url + "/cart", {
            'product_id': product,
            'quantity': random.choice([1,2,3,4,5,10])}, headers={"host": l.host})

    def checkout(l):
        """Simulate checkout process"""
        l.addToCart()
        l.client.post(l.url + "/cart/checkout", {
            'email': 'someone@example.com',
            'street_address': '1600 Amphitheatre Parkway',
            'zip_code': '94043',
            'city': 'Mountain View',
            'state': 'CA',
            'country': 'United States',
            'credit_card_number': '4432801561520454',
            'credit_card_expiration_month': '1',
            'credit_card_expiration_year': '2039',
            'credit_card_cvv': '672',
        }, headers={"host":  l.host})
    
    @task
    def execute_trace(self):
        """
        Main task execution method that replays traces according to original timing
        """
        if self.current_idx >= len(self.trace_data):
            return
        
        current_time = time.time() - self.global_start_time
        app, func, start_time, end_time, duration = self.trace_data[self.current_idx]
        
        # Execute corresponding task based on function mapping
        if (app, func) in self.function_mapping:
            task_name = self.function_mapping[(app, func)]
            if hasattr(self, task_name):
                getattr(self, task_name)()
        
        self.current_idx = (self.current_idx + 1) % len(self.trace_data)

class WebsiteUser(HttpUser):
    """User class for load testing"""
    tasks = [TraceReplayTaskSet]
    wait_time = between(0, 0)   # No wait time as timing is controlled by trace

# Statistics collection setup
stat_file = open('stats.csv', 'w')
requests_per_second = defaultdict(int)

@events.request.add_listener
def hook_request_success(request_type, name, response_time, response_length, response, context, exception, **kw):
    """
    Event listener for request completion
    Records statistics for each request including timing and status
    """
    timestamp = int(time.time() * 1000)
    requests_per_second[timestamp] += 1
    
    if exception:
        stat_file.write(f"{timestamp};{request_type};{requests_per_second[timestamp]};{name};{response_time};ERROR;{str(exception)}\n")
    elif response.status_code >= 400:
        stat_file.write(f"{timestamp};{request_type};{name};{response_time};HTTP_{response.status_code}\n")
    else:
        stat_file.write(f"{timestamp};{request_type};{name};{response_time};SUCCESS\n")

@events.quitting.add_listener
def hook_quitting(environment, **kw):
    """Cleanup handler for test completion"""
    stat_file.close()