# Agent-Based Building Evacuation Simulation

This project is an agent-based simulation for modeling building evacuations. It utilizes the Pygame library to manage the graphical interface and agent dynamics. Agents interact with each other and respond to environmental changes.

## Features
- Real-time simulation of agent movement and interaction.
- Configurable agent attributes, strategies, and environment settings.
- Visual representation of agent behavior and evacuation process.

## Prerequisites
- Python 3.8 or newer installed on your system.
- Git installed for cloning the repository.

## Setting Up the Environment
To run the simulation, follow these steps:

### Step 1: Clone the Repository
Use the following command to clone the project repository to your local machine:
```bash
git clone [url]
```

### Step 2: Create a Conda Environment
Navigate to the project directory and create a Conda environment using the `requirements.txt` file:
```bash
cd project-repository
conda create --name evacuation-sim --file requirements.txt
```
Activate the Conda environment:
```bash
conda activate evacuation-sim
```

### Step 3: Install Additional Dependencies
Ensure all dependencies, such as Pygame, are installed:
```bash
pip install -r requirements.txt
```

## Running the Simulation
1. **Create or Modify the Configuration File:**
   - The simulation uses a YAML file for configuration. This file specifies parameters like the number of agents, their strategies, and environmental settings.
   - An example configuration file, `example_config.yaml`, is provided in the repository. You can modify it to suit your needs.

   Example configuration:
   ```yaml
   simulation:
     agents:
       count: 50
       strategies:
         nearest_exit: 15
         safest_exit: 35
     families:
       count: 10
     agent_attributes:
       health: 100
       communicates: true
   ```

   Ensure the file maintains proper formatting and indentation.

2. **Run the Simulation Script:**
   Execute the main simulation script:
   ```bash
   python run_simulation.py
   ```

3. **Observe the Simulation:**
   - Agents will navigate according to their strategies.
   - Movements and interactions will be visualized in the Pygame window.

## Additional Notes
- **Default Values:** If a configuration parameter is not specified, the simulation will use default values to ensure proper execution.
- **Documentation:** Detailed documentation and comments are available in the codebase for better understanding and customization.

## Repository Structure
- `run_simulation.py`: Main script to execute the simulation.
- `requirements.txt`: List of dependencies for the project.
- `example_config.yaml`: Sample configuration file for reference.
- `README.md`: Instructions and details about the project.

## License
This project is distributed under the MIT License. See `LICENSE` for more information.

