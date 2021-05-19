import gym
import gym_chessven
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines import PPO2
env = gym.make('gym_chessven:chessven-v0')
actions = []
spaces = env.action_space
for action in range(spaces.n):
    actions.append(f'{action}: {env.action_to_move(action)}')
with open('out_test.txt', 'w') as file:
    for i in actions:
        file.write(i + "\n")