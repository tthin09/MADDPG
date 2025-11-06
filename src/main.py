import os
import sys
import argparse
import matplotlib.pyplot as plt
import datetime

from env import TrafficEnv
from maddpg import MADDPG
from utils import get_average_travel_time


parser = argparse.ArgumentParser()
parser.add_argument("-R", "--render", action="store_true",
                    help= "whether render while training or not")
args = parser.parse_args()

path_sumocfg = "./scenario/gen0611/vietnamese_traffic_3x3/simulation.sumocfg"
path_tripinfo = "./scenario/gen0611/vietnamese_traffic_3x3/tripinfo.xml"

if __name__ == "__main__":

    # Before the start, should check SUMO_HOME is in your environment variables
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    # config
    n_episode = 100
    max_step_per_ep = 360 # 3600s because each step = 10s
    
    # init env
    env = TrafficEnv(path_sumocfg, "gui") if args.render else TrafficEnv(path_sumocfg)
    initial_state = env.reset()
    
    # get dimensions (num lane & intersections & n_phase of traffic light)
    n_agents = initial_state.shape[0]
    state_dim = initial_state.shape[1]
    action_dim = env.n_phase
    
    # Close connection after getting dimensions
    env.close()

    # Create an Environment and RL Agent
    agent = MADDPG(n_agents, state_dim, action_dim)
    print(f"Actor output dim: {agent.actors[0].layers[-1].out_features}")

    # Train your RL agent
    performance_list = []
    for episode in range(n_episode):

        state = env.reset()
        reward_epi = []
        actions = [None for _ in range(n_agents)]
        action_probs = [None for _ in range(n_agents)]
        done = False

        step_count = 0
        while not done and step_count <= max_step_per_ep:
            step_count += 1
            # select action according to a given state
            for i in range(n_agents):
                action, action_prob = agent.select_action(state[i, :], i)
                actions[i] = action
                action_probs[i] = action_prob

            if step_count % 90 == 0:
                print(f"Step: {step_count}, action: {actions}")
            
            # apply action and get next state and reward
            before_state = state
            state, reward, done = env.step(actions)

            # make a transition and save to replay memory
            transition = [before_state, action_probs, state, reward, done]
            agent.push(transition)

            # train an agent
            if agent.train_start():
                for i in range(n_agents):
                    agent.train_model(i)
                agent.update_eps()

            if done:
                break
            

        env.close()
        average_traveling_time = get_average_travel_time(path_tripinfo)
        performance_list.append(average_traveling_time)

        print(f"Episode: {episode+1}\t Average Traveling Time:{average_traveling_time}\t Eps:{agent.eps}")

    # Save the model
    agent.save_model("results/trained_model.th")

    # Plot the performance
    plt.style.use('ggplot')
    plt.figure(figsize=(10.8, 7.2), dpi=120)
    plt.plot(performance_list)
    plt.xlabel('# of Episodes')
    plt.ylabel('Average Traveling Time')
    plt.title('Performance of MADDPG for controlling traffic lights')
    plt.savefig(f'./results/performance_{datetime.datetime.now().strftime("%H%M%S")}.png')