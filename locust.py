#!/usr/bin/python
import time
import csv
from collections import defaultdict
import random
from locust import HttpUser, TaskSet, between, events, task
from typing import Dict, List, Tuple, Set
import os
import logging
import json
import os

IP = os.getenv('IP')  
PORT = os.getenv('PORT', '80') 


from collections import defaultdict
def create_function_mapping(trace_file_path, desired_tasks):
    """
    Creates two structures:
    1. Sorted array of (app, function, start_time) tuples
    2. Dictionary mapping (app, function) -> task_name
    """
    func_counts = {}
    trace_events = []
    
    with open(trace_file_path, 'r') as f:
        next(f)  # Skip header
        for line in f:
            app, func, end_timestamp, duration = line.strip().split(',')
            end_time = float(end_timestamp)
            duration = float(duration)
            start_time = end_time - duration
            
            if end_time <= 1000:  # First 5 minutes
                func_counts[func] = func_counts.get(func, 0) + 1
                trace_events.append((app, func, start_time))
    
    sorted_events = sorted(trace_events, key=lambda x: x[2])
    
    sorted_funcs = sorted(
        [(func, count) for func, count in func_counts.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    total_weight = sum(desired_tasks.values())
    sorted_tasks = sorted(
        [(task, count) for task, count in desired_tasks.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    function_mapping = {}
    current_func_idx = 0
    
    for task, weight in sorted_tasks:
        target_percentage = weight / total_weight
        target_calls = int(len(trace_events) * target_percentage + 0.5)
        
        calls_mapped = 0
        while calls_mapped < target_calls and current_func_idx < len(sorted_funcs):
            func = sorted_funcs[current_func_idx][0]
            count = sorted_funcs[current_func_idx][1]
            current_func_idx += 1
            calls_mapped += count
            
            # For each function, map all its appearances in the trace
            for app, f, _ in trace_events:
                if f == func:
                    function_mapping[(app, f)] = task
    
    # Print analysis
    print("\nMapping Analysis:")
    task_counts = defaultdict(int)
    for app, func, _ in sorted_events:
        if (app, func) in function_mapping:
            task = function_mapping[(app, func)]
            task_counts[task] += 1
    
    for task, count in task_counts.items():
        print(f"\n{task}:")
        print(f"Actual calls: {count}")
        print(f"Target weight: {desired_tasks[task]}/{total_weight}")
    
    return {
        'sorted_events': sorted_events,  # List of (app, func, start_time)
        'function_mapping': function_mapping  # Dict of (app, func) -> task_name
    }

# Configuration
host = "kn-frontend.default.127.0.0.1.sslip.io"
url = f"http://{IP}:{PORT}"
print(url)
products = [
    '0PUK6V6EV0', '1YMWWN1N4O', '2ZYFJ3GM2N', '66VCHSJNUP',
    '6E92ZMYYFZ', '9SIQT8TOJO', 'L9ECAV7KIM', 'LS4PSXUNUM', 'OLJCESPC7Z'
]

tasks = {
    'index': 1,
    'setCurrency': 2,
    'browseProduct': 10,
    'addToCart': 2,
    'viewCart': 3,
    'checkout': 1
}
mapping_result = create_function_mapping('/users/Jch270/zero-scaling/AzureFunctionsInvocationTrace.txt', tasks)

class TraceReplayTaskSet(TaskSet):
    """Each user follows the trace timing exactly"""
    
    # Class-level variables shared by all users
    trace_data = None
    function_mapping = None
    global_start_time = None
    
    @classmethod
    def setup_trace_data(cls):
        if cls.trace_data is None:
            # Load mapping data
            cls.trace_data = mapping_result['sorted_events']
            cls.function_mapping = mapping_result['function_mapping']
            cls.global_start_time = time.time()
    
    def on_start(self):
        self.setup_trace_data()
        self.current_idx = 0
    
    def index(l):
        l.client.get(url + "/", headers={"host": host})

    def setCurrency(l):
        currencies = ['EUR', 'USD', 'JPY', 'CAD']
        l.client.post(url + "/setCurrency",
            {'currency_code': random.choice(currencies)}, headers={"host": host})

    def browseProduct(l):
        l.client.get(url + "/product/" + random.choice(products), headers={"host": host})

    def viewCart(l):
        l.client.get(url + "/cart", headers={"host": host})

    def addToCart(l):
        product = random.choice(products)
        l.client.get(url + "/product/" + product, headers={"host": host})
        l.client.post(url + "/cart", {
            'product_id': product,
            'quantity': random.choice([1,2,3,4,5,10])}, headers={"host": host})

    def checkout(l):
        addToCart(l)
        l.client.post(url + "/cart/checkout", {
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
        }, headers={"host":  host})
    
    @task
    def execute_trace(self):
        if self.current_idx >= len(self.trace_data):
            return
        
        current_time = time.time() - self.global_start_time
        app, func, target_time = self.trace_data[self.current_idx]
        
        # If it's not time for the next event, wait
        if current_time < target_time:
            time.sleep(target_time - current_time)
        
        # Execute the corresponding task
        if (app, func) in self.function_mapping:
            task_name = self.function_mapping[(app, func)]
            if hasattr(self, task_name):
                getattr(self, task_name)()
                # getattr(self, task_name)()
                # getattr(self, task_name)()
                # getattr(self, task_name)()
                # getattr(self, task_name)()
                # getattr(self, task_name)()
                # getattr(self, task_name)()
                # getattr(self, task_name)()
        
        self.current_idx = (self.current_idx + 1) % len(self.trace_data)

class WebsiteUser(HttpUser):
    tasks = [TraceReplayTaskSet]
    wait_time = between(0, 0)  # No wait time as timing is controlled by trace

# Stats collection
stat_file = open('stats.csv', 'w')
requests_per_second = defaultdict(int)

@events.request.add_listener
def hook_request_success(request_type, name, response_time, response_length, response, context, exception, **kw):
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
    stat_file.close()