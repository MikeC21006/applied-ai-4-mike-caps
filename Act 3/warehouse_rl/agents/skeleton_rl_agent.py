#!/usr/bin/env python3
"""
Skeleton Optimization Agent - Template for students to implement optimization algorithms

IMPORTANT: This is NOT an RL agent - it's a template for 
students to implement their own optimization algorithms (greedy, Hungarian, etc.)

This agent currently makes terrible decisions:
- Random staffing decisions
- No layout optimization 
- Ignores order priorities
- No intelligent assignment logic

Students should replace the naive methods with proper optimization algorithms.
"""

from multiprocessing import managers

import numpy as np
from typing import Dict, Optional
from .standardized_agents import BaselineAgent

class SkeletonOptimizationAgent(BaselineAgent):
    """
    Template for students to implement their own optimization algorithms.
    
    Students should replace the naive methods with:
    - Economic models for staffing decisions
    - Hungarian algorithm for order assignment  
    - Greedy search for layout optimization
    - Multi-objective optimization techniques
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # Enable unlimited hiring for true economic optimization
        self.env._unlimited_hiring = False
        
        # Students can add their own state tracking here
        self.performance_metrics = []
        self.decision_history = []
        
        # Students can add algorithm parameters here
        # Example: Hungarian algorithm matrices, greedy search parameters, etc.
        self.staffing_parameters = {
            'hire_threshold_ratio': 3.0,
            'fire_threshold_ratio': 2.0,
            'profit_threshold': 0
        }
        
        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False
        
    def reset(self):
        """Reset agent state - students should expand this"""
        self.action_history = []
        self.reward_history = []
        # TODO: Reset any neural network states, replay buffers, etc.
    
    def get_action(self, observation: Dict) -> Dict:
        """
        Generate action based on observation.
        Current implementation is intentionally terrible - students should improve!
        """
        
        # Extract basic info from observation
        current_timestep = observation['time'][0]
        financial_state = observation['financial']  # [profit, revenue, costs, burn_rate]
        queue_info = observation['order_queue']
        employee_info = observation['employees']
        
        action = {
            'staffing_action': self._get_naive_staffing_action(financial_state, employee_info, current_timestep),
            'layout_swap': self._get_naive_layout_action(current_timestep),
            'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)
        }
        
        # TODO: Students should implement proper action recording for optimization
        self.action_history.append(action.copy())
        
        return action
    
    def _get_naive_staffing_action(self, financial_state, employee_info, current_timestep):
        """Adjust staffing based on queue size and profit."""

        # Make staffing decisions every 100 steps.
        if current_timestep % 100 != 0:
            return 0

        queue_length = len(self.env.order_queue.orders)
        total_employees = len(self.env.employees)
        current_profit = float(financial_state[0])

        workers = sum(
            1 for employee in self.env.employees
            if not employee.is_manager
        )

        managers = sum(
            1 for employee in self.env.employees
            if employee.is_manager
        )

        # Maintain at least 5 workers.
        if workers < 5:
            return 1

        # Hire a manager if none exists.
        if managers == 0:
            return 3

        # Add workers when the queue is too large.
        if queue_length / max(1, total_employees) > 4:
            if current_profit > 2000 and total_employees < self.env.max_employees:
                return 1

        return 0
    
    def _get_naive_layout_action(self, current_timestep) -> list:
        """Move frequently accessed items closer to the delivery area."""

        if current_timestep % 100 != 0:
            return [0, 0]

        grid = self.env.warehouse_grid
        frequencies = grid.item_access_frequency

        if frequencies is None or len(frequencies) == 0:
            return [0, 0]

        frequency_values = np.asarray(frequencies).flatten()
        hot_threshold = np.percentile(frequency_values, 75)

        delivery_positions = getattr(
            grid,
            "truck_bay_positions",
            [(grid.width // 2, grid.height // 2)]
        )

        best_swap = [0, 0]
        best_improvement = 1

        for item_id, frequency in enumerate(frequency_values):
            if frequency < hot_threshold:
                continue

            item_locations = grid.find_item_locations(item_id)

            if not item_locations:
                continue

            current_pos = item_locations[0]

            current_distance = min(
                abs(current_pos[0] - delivery[0])
                + abs(current_pos[1] - delivery[1])
                for delivery in delivery_positions
            )

            if current_distance <= 3:
                continue

            for y in range(grid.height):
                for x in range(grid.width):

                    if grid.cell_types[y, x] != 1:
                        continue

                    new_distance = min(
                        abs(x - delivery[0]) + abs(y - delivery[1])
                        for delivery in delivery_positions
                    )

                    improvement = current_distance - new_distance

                    if improvement > best_improvement:
                        current_index = (
                            current_pos[1] * grid.width + current_pos[0]
                        )
                        target_index = y * grid.width + x

                        best_improvement = improvement
                        best_swap = [current_index, target_index]

        if best_swap != [0, 0]:
            return best_swap

        return self._find_cooccurrence_swap()

    
    def _find_cooccurrence_swap(self):
        """Find a swap that brings frequently ordered items closer together."""

        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence

        best_swap = [0, 0]
        best_benefit = 0

        for item1 in range(grid.num_item_types):
            for item2 in range(item1 + 1, grid.num_item_types):
                frequency = cooccurrence[item1, item2]

                if frequency < 3:
                    continue

                locations1 = grid.find_item_locations(item1)
                locations2 = grid.find_item_locations(item2)

                if not locations1 or not locations2:
                    continue

                pos1 = locations1[0]
                pos2 = locations2[0]

                current_distance = grid.manhattan_distance(pos1, pos2)

                if current_distance < 4:
                    continue

                for target_x, target_y in grid.storage_positions:
                    target_pos = (target_x, target_y)

                    if target_pos == pos1 or target_pos == pos2:
                        continue

                    target_item = grid.get_item_at_position(target_x, target_y)

                    if target_item is None:
                        continue

                    new_distance = grid.manhattan_distance(pos1, target_pos)
                    improvement = current_distance - new_distance

                    if improvement <= 0:
                        continue

                    benefit = frequency * improvement

                    if benefit > best_benefit:
                        current_index = pos2[1] * grid.width + pos2[0]
                        target_index = target_y * grid.width + target_x

                        best_benefit = benefit
                        best_swap = [current_index, target_index]

        return best_swap
    
    def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
        """Assign pending orders to idle workers using item distance."""

        assignments = [0] * 20
        orders = self.env.order_queue.orders
        employees = self.env.employees
        grid = self.env.warehouse_grid

        # Find idle workers who are not managers.
        idle_workers = []

        for employee_idx, employee in enumerate(employees):
            state = str(employee.state).upper()

            if not employee.is_manager and state.endswith("IDLE"):
                idle_workers.append(employee_idx)

        # Consider only pending orders, without changing queue order.
        pending_orders = [
            (order_idx, order)
            for order_idx, order in enumerate(orders[:20])
            if order.status == "pending"
        ]

        # Match each idle worker to the closest available pending order.
        while idle_workers and pending_orders:
            best_worker_idx = None
            best_order_idx = None
            best_distance = float("inf")

            for worker_idx in idle_workers:
                employee = employees[worker_idx]

                for order_idx, order in pending_orders:
                    closest_distance = float("inf")

                    for item_type in order.items:
                        for location in grid.find_item_locations(item_type):
                            distance = grid.manhattan_distance(
                                employee.position, location
                            )

                            if distance < closest_distance:
                                closest_distance = distance

                    if closest_distance < best_distance:
                        best_distance = closest_distance
                        best_worker_idx = worker_idx
                        best_order_idx = order_idx

            # Stop if no valid worker-order match was found.
            if best_worker_idx is None or best_order_idx is None:
                break

            # Assignment slot corresponds to the order's queue index.
            assignments[best_order_idx] = best_worker_idx + 1

            idle_workers.remove(best_worker_idx)
            pending_orders = [
                pair for pair in pending_orders
                if pair[0] != best_order_idx
            ]

        return assignments
    
    def record_reward(self, reward: float):
        """
        WEEK 3 STEP 1: Reward tracking and learning - students should expand this
        
        TODO WEEK 3 STEP 1: Students should implement:
        - Proper reward tracking
        - Performance analysis
        - Adaptive parameter adjustment
        - Multi-objective optimization
        """
        self.reward_history.append(reward)
        
        # Skeleton optimization - doesn't actually learn anything useful
        if len(self.reward_history) > 10:
            # "Update" weights randomly (this doesn't actually improve performance)
            if reward > 0:
                self.staffing_weights += np.random.randn(4) * 0.01
                self.layout_weights += np.random.randn(3) * 0.01
    
    def should_update_policy(self) -> bool:
        """
        WEEK 3 STEP 2: Policy updates and adaptation - students should improve this
        
        TODO WEEK 3 STEP 2: Students should implement proper update schedules
        """
        return len(self.action_history) % 50 == 0  # Arbitrary update frequency
    
    def get_performance_metrics(self) -> Dict:
        """
        Get agent performance metrics for analysis
        Students can use this to debug their improvements
        """
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": 0}
        
        return {
            "avg_reward": np.mean(self.reward_history[-100:]),  # Last 100 rewards
            "total_actions": len(self.action_history),
            "exploration_rate": self.exploration_rate,
            "recent_performance": np.mean(self.reward_history[-10:]) if len(self.reward_history) >= 10 else 0
        }


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    """Factory function to create skeleton Optimization agent"""
    return SkeletonOptimizationAgent(env)


# TODO: Students should implement these advanced components:

class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """
    Template for students to implement their improved Optimization agent
    
    Suggested improvements:
    1. Replace random staffing with demand-based hiring
    2. Implement proper layout optimization using item frequencies
    3. Add distance-based order assignment
    4. Implement basic Q-optimization or policy gradients
    5. Add proper exploration vs exploitation balance
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # TODO: Students implement these
        # self.q_table = {}
        # self.policy_network = SimpleNeuralNetwork()
        # self.experience_buffer = []
        # self.target_network = None
        
    def _get_improved_staffing_action(self, financial_state, employee_info, queue_info):
        """
        WEEK 2 STEP 1: Students implement intelligent staffing:
        - Hire when queue is growing
        - Fire when queue is empty for extended periods
        - Consider profit margins before hiring
        - Balance managers vs workers
        """
        pass
    
    def _get_improved_layout_action(self, observation):
        """
        WEEK 1 STEP 1: Students implement smart layout optimization:
        - Move frequently accessed items closer to delivery
        - Group items that are often ordered together
        - Only optimize when queue is manageable
        - Track swap effectiveness
        """
        pass
    
    def _get_improved_order_assignments(self, queue_info, employee_info):
        """
        WEEK 2 STEP 2: Students implement efficient order assignment:
        - Assign orders to closest available employees
        - Prioritize high-value or urgent orders
        - Consider employee current locations
        - Balance workload across employees
        """
        pass
    
    def learn_from_experience(self, state, action, reward, next_state, done):
        """
        WEEK 3 STEP 3: Students implement multi-objective optimization:
        - Performance trend analysis
        - Adaptive parameter tuning
        - Multi-objective trade-off handling
        - Robust optimization techniques
        """
        pass