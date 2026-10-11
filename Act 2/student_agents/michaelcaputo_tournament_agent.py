#!/usr/bin/env python
"""
Tournament Agent: Hulk
Student: Michael Caputo
Generated: 2026-10-02 17:36:10

Evolution Details:
- Generations: 100
- Final Fitness: 134.2
- Trained against: Gradual, Generous Tit-for-Tat, Hard Majority, Grim Trigger, Pavlov...

Strategy: destroy everything in sight
"""

from agents import Agent, INVEST, UNDERCUT
import random


class MichaelCaputoAgent(Agent):
    """
    Hulk

    destroy everything in sight

    Evolved Genes: [1.0, 1.0, 1.0, 0.0, 0.14415546620713768, 0.39808269999137247]
    """

    def __init__(self):
        # These genes were evolved through 100 generations
        self.genes = [1.0, 1.0, 1.0, 0.0, 0.14415546620713768, 0.39808269999137247]

        # Required for tournament compatibility
        self.student_name = "Michael Caputo"

        super().__init__(
            name="Hulk",
            description="destroy everything in sight"
        )

    def choose_action(self) -> bool:
        """
        IMPROVED decision logic - AGGRESSIVE VERSION
        More likely to retaliate, less exploitable
        """

        # First 3 rounds: use initial cooperation gene
        if self.round_num < 3:
            return random.random() < self.genes[0]

        # Calculate memory window
        memory_length = max(1, int(self.genes[4] * 10) + 1)
        recent_history = self.history[-memory_length:]
        cooperation_rate = sum(recent_history) / len(recent_history)

        # AGGRESSIVE STRATEGY: Higher threshold for cooperation

        # Only cooperate if opponent is VERY cooperative (>80%)
        if cooperation_rate > 0.8:
            return random.random() < self.genes[1]  # gene[1] should evolve HIGH

        # If somewhat cooperative (50-80%), be cautious
        elif cooperation_rate > 0.5:
            # Mix of cooperation and defection
            coop_prob = (
                self.genes[1] * self.genes[2]
                * (cooperation_rate - 0.5) * 2
            )
            return random.random() < coop_prob

        # If aggressive (<50%), retaliate hard
        else:
            # Mostly defect, with small chance to forgive
            if random.random() < self.genes[3] * self.genes[5] * 0.3:
                return INVEST
            else:
                return UNDERCUT



# Convenience function for tournament loading
def get_agent():
    """Return an instance of this agent for tournament use"""
    return MichaelCaputoAgent()


if __name__ == "__main__":
    # Test that the agent can be instantiated
    agent = get_agent()
    print(f"✅ Agent loaded successfully: {agent.name}")
    print(f"   Genes: {agent.genes}")
    print(f"   Description: {agent.description}")
