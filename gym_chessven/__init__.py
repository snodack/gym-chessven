from gym.envs.registration import register

register(
    id='chessven-v0',
    entry_point='gym_chessven.envs:Chess_Environment'
)
