import traci
from sumolib import checkBinary
import numpy as np


class TrafficEnv:
    def __init__(self, path_sumocfg, mode='binary'):
        # If the mode is 'gui', it renders the scenario.
        if mode == 'gui':
            self.sumoBinary = checkBinary('sumo-gui')
        else:
            self.sumoBinary = checkBinary('sumo')
        self.sumoCmd = [self.sumoBinary, "-c", path_sumocfg, '--no-step-log', '-W']

        self.time = None
        self.decision_time = 10
        self.n_intersections = None
        self.n_phase = None
        self.max_lanes = None

    def reset(self):
        traci.start(self.sumoCmd)
        traci.simulationStep()
        self.time = 0
        
        # Set number of intersections dynamically
        self.n_intersections = len(traci.trafficlight.getIDList())
        
        # Find max number of controlled lanes across all intersections
        self.max_lanes = max(
            len(set(traci.trafficlight.getControlledLanes(tl_id))) 
            for tl_id in traci.trafficlight.getIDList()
        )
        
        # Get the actual number of phases from the first traffic light
        # (assuming all traffic lights have the same number of phases)
        first_tl = traci.trafficlight.getIDList()[0]
        logic = traci.trafficlight.getAllProgramLogics(first_tl)[0]
        all_phases = len(logic.phases)

        # We have multiple phases, but we only care on 2 phases: Green and Red
        self.n_phase = 2
        self.phase_mapping = [0, 2]

        return self.get_state()

    def get_state(self):
        # state: N X D array, where N is the number of traffic lights and D is the dimension of each observation
        state = []
        for i, intersection_ID in enumerate(traci.trafficlight.getIDList()):
            observation = []
            for lane in traci.trafficlight.getControlledLanes(intersection_ID):
                observation.append(traci.lane.getLastStepVehicleNumber(lane))
                observation.append(traci.lane.getLastStepHaltingNumber(lane))
                
            while len(observation) < self.max_lanes * 2:
                observation.extend([0, 0])

            current_phase = traci.trafficlight.getPhase(intersection_ID)
            mapped_phase = 0 if current_phase in [0, 1] else 1

            phase = [0 for _ in range(self.n_phase)]
            phase[mapped_phase] = 1
            observation = observation + phase
            state.append(observation)

        state = np.array(state)
        return state

    def apply_action(self, actions):
        if len(actions) != self.n_intersections:
            raise ValueError(f"Expected {self.n_intersections} actions, got {len(actions)}")
        
        for i, intersection_ID in enumerate(traci.trafficlight.getIDList()):
            if not isinstance(actions[i], (int, np.integer)):
                raise TypeError(f"Action at index {i} must be int, got {type(actions[i])}: {actions[i]}")
            
            desired_phase = self.phase_mapping[actions[i]]
            current_phase = traci.trafficlight.getPhase(intersection_ID)
            
            current_direction = 0 if current_phase in [0, 1] else 1
            
            if actions[i] != current_direction:
                traci.trafficlight.setPhase(intersection_ID, desired_phase)  # switch to next phase after yellow light

    def step(self, actions):
        self.apply_action(actions)
        for _ in range(self.decision_time):
            traci.simulationStep()
            self.time += 1

        state = self.get_state()
        reward = self.get_reward()
        done = self.get_done()
        return state, reward, done

    def get_reward(self):
        reward = [0.0 for _ in range(self.n_intersections)]
        for i, intersection_ID in enumerate(traci.trafficlight.getIDList()):
            for lane in traci.trafficlight.getControlledLanes(intersection_ID):
                reward[i] += traci.lane.getLastStepHaltingNumber(lane)

        reward = -np.array(reward)
        return reward

    def get_done(self):
        return traci.simulation.getMinExpectedNumber() == 0

    def close(self):
        traci.close()


if __name__ == "__main__":
    env = TrafficEnv()
    state = env.reset()
