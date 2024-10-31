import logging
from swarm.repl import run_demo_loop

from agents import default_context, base_agent


if __name__ == "__main__":
    print("Welcome to the Daily Life Automation Demo!")
    print("You can interact with the Triage Agent, who will direct you to other agents as needed.")
    print("Type 'exit' to end the demo.")
    print("\nHow can I assist you today?")

    logging.basicConfig(level=logging.DEBUG)

    # Run the demo loop with the triage agent
    run_demo_loop(base_agent, stream=True, context_variables=default_context)
