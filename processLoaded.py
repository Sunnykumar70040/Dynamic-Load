import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import random
import time
import threading
from queue import Queue
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class Processor:
    def __init__(self, id, capacity=100, processing_speed=1.0):
        self.id = id
        self.capacity = capacity  # Maximum load capacity
        self.processing_speed = processing_speed  # Speed multiplier
        self.current_load = 0  # Current load (0-100%)
        self.tasks = []  # List of tasks currently assigned
        self.history = []  # History of load values for plotting
        
    def add_task(self, task):
        self.tasks.append(task)
        self.current_load += task.load
        
    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            self.current_load -= task.load
            
    def process_tasks(self):
        # Process tasks based on processing speed
        completed_tasks = []
        for task in self.tasks:
            task.remaining_time -= self.processing_speed
            if task.remaining_time <= 0:
                completed_tasks.append(task)
                
        # Remove completed tasks
        for task in completed_tasks:
            self.remove_task(task)
        
    # Update history
        self.update_history()
        
        return completed_tasks

    def update_history(self):
        # Record history for plotting
        self.history.append(self.current_load)
        if len(self.history) > 100:  # Keep only last 100 points
            self.history = self.history[-100:]
    
    def get_available_capacity(self):
        return self.capacity - self.current_load

class Task:
    def __init__(self, id, load, execution_time):
        self.id = id
        self.load = load  # CPU load (0-100%)
        self.execution_time = execution_time  # Time to complete
        self.remaining_time = execution_time  # Remaining time
        self.processor = None  # Assigned processor

class LoadBalancer:
    def __init__(self, num_processors=4):
        self.processors = [Processor(i) for i in range(num_processors)]
        self.task_queue = Queue()
        self.completed_tasks = 0
        self.task_id_counter = 0
        self.algorithm = "round_robin"  # Default algorithm
        self.running = False
        self.paused = False
        
    def add_task(self, load, execution_time):
        task = Task(self.task_id_counter, load, execution_time)
        self.task_id_counter += 1
        self.task_queue.put(task)
        
    def distribute_tasks(self):
        # Distribute tasks from queue to processors based on selected algorithm
        while not self.task_queue.empty():
            task = self.task_queue.get()
            
            if self.algorithm == "round_robin":
                self._round_robin(task)
            elif self.algorithm == "least_loaded":
                self._least_loaded(task)
            elif self.algorithm == "weighted":
                self._weighted_distribution(task)
            elif self.algorithm == "adaptive":
                self._adaptive_distribution(task)
                
    def _round_robin(self, task):
        # Simple round-robin assignment
        assigned = False
        for processor in self.processors:
            if processor.get_available_capacity() >= task.load:
                processor.add_task(task)
                assigned = True
                break
                
        # If no processor has capacity, assign to the first one anyway
        if not assigned and self.processors:
            self.processors[0].add_task(task)
            
    def _least_loaded(self, task):
        # Assign to processor with least current load
        processors = sorted(self.processors, key=lambda p: p.current_load)
        if processors and processors[0].get_available_capacity() >= task.load:
            processors[0].add_task(task)
        elif processors:  # Assign anyway if all are overloaded
            processors[0].add_task(task)
            
    def _weighted_distribution(self, task):
        # Distribute based on processing speed
        processors = sorted(self.processors, 
                           key=lambda p: p.current_load / p.processing_speed)
        if processors and processors[0].get_available_capacity() >= task.load:
            processors[0].add_task(task)
        elif processors:
            processors[0].add_task(task)
            
    def _adaptive_distribution(self, task):
        # Adaptive algorithm that considers both load and processing speed
        # and adjusts based on recent performance
        
        # Calculate a score for each processor
        scores = []
        for p in self.processors:
            # Lower score is better
            recent_load = sum(p.history[-10:]) / max(len(p.history[-10:]), 1)
            score = (p.current_load / p.capacity) * (1 / p.processing_speed) * (1 + recent_load/200)
            scores.append((p, score))
            
        # Sort by score (lower is better)
        processors = [p for p, _ in sorted(scores, key=lambda x: x[1])]
        
        if processors and processors[0].get_available_capacity() >= task.load:
            processors[0].add_task(task)
        elif processors:
            processors[0].add_task(task)
            
    def process_cycle(self):
        # Process one cycle of tasks on all processors
        completed = []
        for processor in self.processors:
            # Make sure history is updated even if no tasks are processed
            if not processor.tasks:
                processor.update_history()
            completed.extend(processor.process_tasks())
        
        self.completed_tasks += len(completed)
        return completed
        
    def run_simulation(self, task_generator, update_callback):
        self.running = True
        while self.running:
            if not self.paused:
                # Generate new tasks
                new_tasks = task_generator()
                for load, exec_time in new_tasks:
                    # self.add_task(load, time)
                    self.add_task(load, exec_time)
                
                # Distribute tasks from queue
                self.distribute_tasks()
                
                # Process tasks on processors
                self.process_cycle()
                
                # Update UI
                update_callback()
                
            time.sleep(0.1)  # Simulation speed

class LoadBalancerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Load Balancer Simulation")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Create load balancer with default 4 processors
        self.load_balancer = LoadBalancer(4)
        
        # Create UI components
        self.create_ui()
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self.load_balancer.run_simulation, 
                                                args=(self.generate_tasks, self.update_ui))
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel (left side)
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Algorithm selection
        ttk.Label(control_frame, text="Load Balancing Algorithm:").pack(anchor=tk.W, pady=5)
        self.algorithm_var = tk.StringVar(value=self.load_balancer.algorithm)
        algorithms = ["round_robin", "least_loaded", "weighted", "adaptive"]
        algorithm_menu = ttk.Combobox(control_frame, textvariable=self.algorithm_var, 
                                     values=algorithms, state="readonly")
        algorithm_menu.pack(fill=tk.X, pady=5)
        algorithm_menu.bind("<<ComboboxSelected>>", self.change_algorithm)
        
        # Number of processors
        ttk.Label(control_frame, text="Number of Processors:").pack(anchor=tk.W, pady=5)
        self.processor_var = tk.IntVar(value=4)
        processor_scale = ttk.Scale(control_frame, from_=1, to=16, 
                                   variable=self.processor_var, orient=tk.HORIZONTAL)
        processor_scale.pack(fill=tk.X, pady=5)
        processor_scale.bind("<ButtonRelease-1>", self.change_processors)
        self.processor_label = ttk.Label(control_frame, text="4")
        self.processor_label.pack(anchor=tk.W)
        
        # Task generation rate
        ttk.Label(control_frame, text="Task Generation Rate:").pack(anchor=tk.W, pady=5)
        self.task_rate_var = tk.DoubleVar(value=1.0)
        task_rate_scale = ttk.Scale(control_frame, from_=0.1, to=5.0, 
                                   variable=self.task_rate_var, orient=tk.HORIZONTAL)
        task_rate_scale.pack(fill=tk.X, pady=5)
        self.task_rate_label = ttk.Label(control_frame, text="1.0 tasks/sec")
        self.task_rate_label.pack(anchor=tk.W)
        task_rate_scale.bind("<Motion>", self.update_task_rate_label)
        
        # Task size
        ttk.Label(control_frame, text="Average Task Size:").pack(anchor=tk.W, pady=5)
        self.task_size_var = tk.IntVar(value=20)
        task_size_scale = ttk.Scale(control_frame, from_=5, to=50, 
                                   variable=self.task_size_var, orient=tk.HORIZONTAL)
        task_size_scale.pack(fill=tk.X, pady=5)
        self.task_size_label = ttk.Label(control_frame, text="20% CPU load")
        self.task_size_label.pack(anchor=tk.W)
        task_size_scale.bind("<Motion>", self.update_task_size_label)
        
        # Task duration
        ttk.Label(control_frame, text="Average Task Duration:").pack(anchor=tk.W, pady=5)
        self.task_duration_var = tk.DoubleVar(value=5.0)
        task_duration_scale = ttk.Scale(control_frame, from_=1.0, to=20.0, 
                                      variable=self.task_duration_var, orient=tk.HORIZONTAL)
        task_duration_scale.pack(fill=tk.X, pady=5)
        self.task_duration_label = ttk.Label(control_frame, text="5.0 seconds")
        self.task_duration_label.pack(anchor=tk.W)
        task_duration_scale.bind("<Motion>", self.update_task_duration_label)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        # Stats display
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.queue_label = ttk.Label(stats_frame, text="Tasks in Queue: 0")
        self.queue_label.pack(anchor=tk.W, pady=2)
        
        self.completed_label = ttk.Label(stats_frame, text="Completed Tasks: 0")
        self.completed_label.pack(anchor=tk.W, pady=2)
        
        self.avg_load_label = ttk.Label(stats_frame, text="Average Load: 0%")
        self.avg_load_label.pack(anchor=tk.W, pady=2)
        
        # Visualization panel (right side)
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Processor visualization
        self.processor_frame = ttk.LabelFrame(viz_frame, text="Processors", padding=10)
        self.processor_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create processor displays
        self.processor_displays = []
        self.update_processor_displays()
        
        # Load history graph
        graph_frame = ttk.LabelFrame(viz_frame, text="Load History", padding=10)
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create figure with proper size and DPI for Tkinter
        self.fig, self.ax = plt.subplots(figsize=(6, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize empty plot
        self.ax.set_ylim(0, 100)
        self.ax.set_ylabel("Load (%)")
        self.ax.set_xlabel("Time")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.fig.tight_layout()
        
    def update_processor_displays(self):
        # Clear existing displays
        for widget in self.processor_frame.winfo_children():
            widget.destroy()
            
        # Create new processor displays
        self.processor_displays = []
        for i, processor in enumerate(self.load_balancer.processors):
            frame = ttk.Frame(self.processor_frame, padding=5)
            frame.grid(row=i//2, column=i%2, sticky=tk.NSEW, padx=5, pady=5)
            
            # Processor label
            label = ttk.Label(frame, text=f"Processor {processor.id}")
            label.pack(anchor=tk.W)
            
            # Load bar
            canvas = tk.Canvas(frame, width=200, height=30, bg="#e0e0e0")
            canvas.pack(fill=tk.X, pady=5)
            
            # Task count
            task_label = ttk.Label(frame, text="Tasks: 0")
            task_label.pack(anchor=tk.W)
            
            # Speed control
            speed_frame = ttk.Frame(frame)
            speed_frame.pack(fill=tk.X)
            
            ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
            speed_var = tk.DoubleVar(value=processor.processing_speed)
            speed_scale = ttk.Scale(speed_frame, from_=0.5, to=2.0, 
                                   variable=speed_var, orient=tk.HORIZONTAL)
            speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            speed_label = ttk.Label(speed_frame, text=f"{processor.processing_speed:.1f}x")
            speed_label.pack(side=tk.LEFT)
            
            # Store references
            self.processor_displays.append({
                'frame': frame,
                'canvas': canvas,
                'task_label': task_label,
                'speed_var': speed_var,
                'speed_label': speed_label,
                'processor': processor
            })
            
            # Bind speed change
            speed_scale.bind("<Motion>", lambda e, p=processor, sl=speed_label, sv=speed_var: 
                           self.update_processor_speed(p, sl, sv))
            
        # Configure grid
        for i in range(2):
            self.processor_frame.columnconfigure(i, weight=1)
            
    def update_processor_speed(self, processor, label, var):
        processor.processing_speed = var.get()
        label.config(text=f"{processor.processing_speed:.1f}x")
        
    def update_ui(self):
        # Update processor displays
        for display in self.processor_displays:
            processor = display['processor']
            canvas = display['canvas']
            
            # Update load bar
            canvas.delete("all")
            width = canvas.winfo_width()
            load_width = (processor.current_load / processor.capacity) * width
            
            # Color based on load
            if processor.current_load < 60:
                color = "#4CAF50"  # Green
            elif processor.current_load < 85:
                color = "#FFC107"  # Yellow
            else:
                color = "#F44336"  # Red
                
            canvas.create_rectangle(0, 0, load_width, 30, fill=color, outline="")
            canvas.create_text(width/2, 15, text=f"{processor.current_load:.1f}%", 
                             fill="black", font=("Arial", 10, "bold"))
            
            # Update task count
            display['task_label'].config(text=f"Tasks: {len(processor.tasks)}")
            
        # Update statistics
        self.queue_label.config(text=f"Tasks in Queue: {self.load_balancer.task_queue.qsize()}")
        self.completed_label.config(text=f"Completed Tasks: {self.load_balancer.completed_tasks}")
        
        # Calculate average load
        if self.load_balancer.processors:
            avg_load = sum(p.current_load for p in self.load_balancer.processors) / len(self.load_balancer.processors)
            self.avg_load_label.config(text=f"Average Load: {avg_load:.1f}%")
            
        # Update graph
        self.update_graph()
        
    def update_graph(self):
        self.ax.clear()
    
        # Plot load history for each processor
        for i, processor in enumerate(self.load_balancer.processors):
            if processor.history:
                # Use a different color for each processor
                color = plt.cm.tab10(i % 10)
                self.ax.plot(processor.history, label=f"Processor {i}", color=color, linewidth=2)
    
        # Set proper limits and labels
        self.ax.set_ylim(0, 110)  # Give a little headroom above 100%
        self.ax.set_ylabel("Load (%)")
        self.ax.set_xlabel("Time")
    
        # Add legend with smaller font to save space
        self.ax.legend(loc="upper right", fontsize='small')
        self.ax.grid(True, linestyle='--', alpha=0.7)
    
        # Make sure the figure has a tight layout
        self.fig.tight_layout()
    
        # Force redraw
        self.canvas.draw_idle()
        
    def generate_tasks(self):
        # Generate random tasks based on current settings
        tasks = []
        rate = self.task_rate_var.get()
        
        # Randomly generate tasks based on rate
        if random.random() < rate * 0.1:  # Adjust for simulation speed
            size = max(5, min(100, random.gauss(self.task_size_var.get(), 10)))
            duration = max(1, random.gauss(self.task_duration_var.get(), 2))
            tasks.append((size, duration))
            
        return tasks
        
    def change_algorithm(self, event):
        self.load_balancer.algorithm = self.algorithm_var.get()
        
    def change_processors(self, event):
        num_processors = int(self.processor_var.get())
        self.processor_label.config(text=str(num_processors))
        
        # Update processor count
        current_count = len(self.load_balancer.processors)
        
        if num_processors > current_count:
            # Add processors
            for i in range(current_count, num_processors):
                self.load_balancer.processors.append(Processor(i))
        elif num_processors < current_count:
            # Remove processors and redistribute their tasks
            removed_tasks = []
            for processor in self.load_balancer.processors[num_processors:]:
                for task in processor.tasks:
                    removed_tasks.append(task)
                    
            self.load_balancer.processors = self.load_balancer.processors[:num_processors]
            
            # Put removed tasks back in queue
            for task in removed_tasks:
                self.load_balancer.task_queue.put(task)
                
        # Update UI
        self.update_processor_displays()
        
    def update_task_rate_label(self, event):
        self.task_rate_label.config(text=f"{self.task_rate_var.get():.1f} tasks/sec")
        
    def update_task_size_label(self, event):
        self.task_size_label.config(text=f"{self.task_size_var.get()}% CPU load")
        
    def update_task_duration_label(self, event):
        self.task_duration_label.config(text=f"{self.task_duration_var.get():.1f} seconds")
        
    def toggle_pause(self):
        self.load_balancer.paused = not self.load_balancer.paused
        self.pause_button.config(text="Resume" if self.load_balancer.paused else "Pause")
        
    def reset_simulation(self):
        # Reset the simulation
        num_processors = len(self.load_balancer.processors)
        self.load_balancer = LoadBalancer(num_processors)
        self.load_balancer.algorithm = self.algorithm_var.get()
        
        # Update UI
        self.update_processor_displays()
        
        # Restart simulation thread if needed
        if not self.simulation_thread.is_alive():
            self.simulation_thread = threading.Thread(target=self.load_balancer.run_simulation, 
                                                    args=(self.generate_tasks, self.update_ui))
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoadBalancerApp(root)
    root.mainloop()
