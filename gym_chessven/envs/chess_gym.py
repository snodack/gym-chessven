import gym
import copy
import asyncio
import move_finder as mf
import move_class as mc
import generator_moves as gm
from random import randint
from gym import spaces, error, utils

from stable_baselines import PPO2

CASTLING_REWARD = 1
PAWN_TRANSFORMATON_REWARD = {
            '1': 10,
            '2': 8,
            '3': 5,
            '4': 5
        }
FIGURE_COST_REWARD= {
            'Q': 20,
            'R': 10,
            'B': 10,
            'N': 10,
            'P': 5,
            'K': 10
        }
WIN_REWARD = 100
DRAW_REWARD = -100
LOSE_REWARD = -100
INVALID_ACTION_REWARD = -10
VALID_ACTION_REWARD = 20
LOG = True
global_position = [["bR","bN","bB","bQ","bK","bB","bN","bR"],
                    ["bP","bP","bP","bP","bP","bP","bP","bP"],
                    [None,None,None,None,None,None,None,None],
                    [None,None,None,None,None,None,None,None],
                    [None,None,None,None,None,None,None,None],
                    [None,None,None,None,None,None,None,None],
                    ["wP","wP","wP","wP","wP","wP","wP","wP"],
                    ["wR","wN","wB","wQ","wK","wB","wN","wR"]
]
def check_castling_shah(check_position, player_color, long_castling):
    position = copy.deepcopy(check_position)
    #Если король под шахом ->выход
    if not mf.check_shah(position, player_color):
        return False
    king_file = (int)(7 - 7 * (not player_color))
    position[king_file][4], position[king_file][5 - 2 * long_castling] = None , position[king_file][4]
    if not mf.check_shah(position, player_color):
        return False
    position[king_file][5 - 2 * long_castling], position[king_file][6 - 4 * long_castling] = None , position[king_file][5 - 2 * long_castling]
    if not mf.check_shah(position, player_color):
        return False
    return True

def find_moves(position, player_color, players_castling, stack_move):
    #Возможные ходы
    possible_moves = []
    # Moves without check by shah - ходы которые потенциально не могу быть произведены
    move_wcbs = mf.find_chess_moves(player_color, position, players_castling[player_color], stack_move[-1])
    #Необходимо проверить их
    move_next_position = None
    for i in move_wcbs:
        i_move = i.get_move()
        move_check_result = False
        #Рокировка
        if len(i_move)<4:
            if len(i_move)> 2:
                #Длинная рокировка
                move_check_result = check_castling_shah(position,player_color, True)
            else:
                #Коротка рокировка
                move_check_result = check_castling_shah(position,player_color, False)
        else:
            move_next_position = make_move(position, i, player_color, players_castling, stack_move)[0]
            move_check_result =  mf.check_shah(move_next_position, player_color)
        if move_check_result:
             possible_moves.append(i)
    possible_moves.append(mc.CMove(player_color, ""))
    return possible_moves # for allget_move

def make_move(global_position, i_move, player_color, players_castling, stack_move):
    reward = 0
    move = i_move.get_move()
    position = copy.deepcopy(global_position) #копия глобальной позиции - дабы не портить основу
    castling = copy.deepcopy(players_castling)
    color_figure = 'w' if player_color else 'b'
    # Ходы с превращением пешки
    if len(move) > 4:
        figures = {
            '1': 'Q',
            '2': 'R',
            '3': 'B',
            '4': 'N'
        }
        current_position_figure = ((int)(move[0]), (int)(move[1]))
        next_position_figure = ((int)(move[2]), (int)(move[3]))
        position[next_position_figure[0]][next_position_figure[1]] = color_figure + figures[move[4]]
        position[current_position_figure[0]][current_position_figure[1]] = None
        reward = PAWN_TRANSFORMATON_REWARD[move[4]]
    # Обычные ходы "2233"
    elif len(move) > 3:
        #Разбираем ход
        #Позиция фигуры до хода
        current_position_figure = ((int)(move[0]), (int)(move[1]))
        #Позиция фигуры после хода
        next_position_figure = ((int)(move[2]), (int)(move[3]))
        opp_figure = position[next_position_figure[0]][next_position_figure[1]]
        if opp_figure != None:
            if opp_figure[1] == 'K':
                reward =10
            reward = FIGURE_COST_REWARD[opp_figure[1]]
        figure, position[current_position_figure[0]][current_position_figure[1]] = position[current_position_figure[0]][current_position_figure[1]], None
        position[next_position_figure[0]][next_position_figure[1]] = figure

        # Убираем возможность рокировки, при движении короля
        if figure[1] == 'K':
            castling[player_color] = (False, False)
        # Движение Ладьи справа(сбивает рокировки)
        if (current_position_figure[1] == 7 and current_position_figure[0] == int(7 - 7 * player_color )):
            castling[player_color][0] == False
        # Движение Ладьи слева(сбивает рокировки)
        elif (current_position_figure[1] == 0 and current_position_figure[0] == int(7 - 7 * player_color )):
            castling[player_color][1] == False
        
        last_move = stack_move[-1]
        if (last_move != None and
            last_move.get_allow_aisle() and
            figure[1] == 'P' and 
            global_position[next_position_figure[0]][next_position_figure[1]] == None and
            current_position_figure[1] != next_position_figure[1]):
            cache = last_move.get_to_int()
            position[cache[0]][cache[1]] = None

        
    #Длинная рокировка "000"
    elif len(move) > 2:
        king_file = (int)(7 - 7 * (not player_color))
        #Проверяем нет ли шахов по пути на рокировку
        position[king_file][4], position[king_file][2] = None , position[king_file][4]
        position[king_file][3], position[king_file][0] = position[king_file][7], None
        castling[player_color] = (False, False)
        reward = CASTLING_REWARD
    #Короткая рокировка "00"
    elif (len(move)==2):
        king_file = (int)(7 - 7 * (not player_color))
        position[king_file][4], position[king_file][6] = None , position[king_file][4]
        position[king_file][5], position[king_file][7] = position[king_file][7], None
        castling[player_color] = (False, False)
        reward = CASTLING_REWARD
    elif (move=='#'):
        print(f'action {move}')
        return (position, castling, LOSE_REWARD, True)
    return (position, castling, 0, False)

class Chess_Environment(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self, actor_color = True):
        self.log = []
        self.moves_max = 150
        self.all_moves = gm.get_actions()
        self.observation_space = spaces.Box(-6, 6, (8, 8)) #Поле 8 на 8, 6 разных фигур + 0 = пустое поле
        self.action_space = spaces.Discrete(1792 + 510 + 4)#Передвижение с любой клетки на другую 1792, 8 рядов * 3 клетки от пешки(1 прямо, 2 при рублении) * 4 разные фигуры + сдача
        self.current_color = True
        self.actor_color = actor_color
        self.players_castling = [(True, True), (True, True)]
        self.opponent_type = 0 #random moves
        self.reset()
    def reset(self):
        """
        Resets the state of the environment, returning an initial observation.
        Outputs -> observation : the initial observation of the space. (Initial reward is assumed to be 0.)
        """
        self.game_state = copy.deepcopy(global_position)
        self.prev_state = None
        self.done = False
        self.current_color = True
        self.stack_move = [None]
        self.repetitions = 0  # 3 repetitions ==> DRAW
        self.move_count = 0
        self.players_castling = [(True, True), (True, True)]
        self.to_gym_state()
        self.info = {}

        self.possible_moves = find_moves(self.game_state, self.current_color, self.players_castling, self.stack_move)

        #Если игрок играет за черных
        if not self.actor_color:
            #Рандомный ход компьтера, позже игра против себя
            opponent_move = self.opponent_policy()
            # make move
            self.game_state, self.players_castling, opp_reward, self.done = make_move(self.game_state, opponent_move, self.current_color, self.players_castling, self.stack_move)
            self.stack_move.append(opponent_move)
            self.to_gym_state()
            self.current_color  = not self.current_color
            self.possible_moves = find_moves(self.game_state, self.current_color, self.players_castling, self.stack_move)
        return self.state

    def step(self, action):
        """
        Run one timestep of the environment's dynamics. When end of episode
        is reached, reset() should be called to reset the environment's internal state.
        Input
        -----
        action : an action provided by the environment
        Outputs
        -------
        (observation, reward, done, info)
        observation : agent's observation of the current environment
        reward [Float] : amount of reward due to the previous action
        done : a boolean, indicating whether the episode has ended
        info : a dictionary containing other diagnostic information from the previous action
        """
        # validate action
        #assert self.action_space.contains(action), "ACTION ERROR {}".format(action)

        # action invalid in current state
        action_as_move = self.action_to_move(action)
        action_to_game = None
        for i in self.possible_moves:
            if i.get_move() == action_as_move and not i.is_pt():
                action_to_game = i
                break
            elif len(action_as_move) == 5 and i.get_move() == action_as_move[0:4] and  i.is_pt():
                action_to_game = i
                action_to_game.trans_to_figure(action_as_move[4])

        
        #invalid moves reward
        if action_to_game == None:
            reward = INVALID_ACTION_REWARD
            return self.state, reward, self.done, self.info


        # Game is done
        if self.done:
            return (
                self.state,
                0.0,
                True,
                self.info,
            )
        if self.move_count > self.moves_max:
            return (
                self.state,
                DRAW_REWARD,
                True,
                self.info,
            )
        self.move_count +=1
        # valid action reward
        reward = VALID_ACTION_REWARD
        # make move
        self.game_state, self.players_castling, move_reward, self.done = make_move(self.game_state, action_to_game, self.current_color, self.players_castling, self.stack_move)
        self.stack_move.append(action_to_game)
        self.to_gym_state()
        reward += move_reward
        if self.done:
            return self.state, reward, self.done, self.info
        # opponent play
        self.current_color  = not self.current_color
        self.possible_moves = find_moves(self.game_state, self.current_color, self.players_castling, self.stack_move)
        # check if there are no possible_moves for opponent
        if not self.possible_moves:
            # mat
            if not mf.check_shah(self.game_state, self.current_color):
                if LOG:
                    color = "white" if self.current_color else "black"
                    print(color + " lose!")
                self.done = True
                reward += WIN_REWARD
            else:#pat
                if LOG:
                    print("pat")
                    reward += DRAW_REWARD
        if self.done:
            return self.state, reward, self.done, self.info

        # Bot Opponent play
        opponent_move = self.opponent_policy()
        # make move
        self.game_state, self.players_castling, opp_reward, self.done = make_move(self.game_state, opponent_move, self.current_color, self.players_castling, self.stack_move)
        self.to_gym_state()
        self.current_color  = not self.current_color
        self.possible_moves = find_moves(self.game_state, self.current_color, self.players_castling, self.stack_move)
        reward -= opp_reward
        # check if there are no possible_moves for opponent
        if not self.possible_moves: # mat
            if not mf.check_shah(self.game_state, self.current_color):
                if LOG:
                    color = "white" if self.current_color else "black"
                    print(color + " lose!")
                self.done = True
                reward += LOSE_REWARD
            else:#pat
                if LOG:
                    print("pat")
                    reward += DRAW_REWARD

        return self.state, reward, self.done, self.info

    def action_to_move(self, action):
        #not default move
        if action >= 1792:
            _action = action - 1792
            #00 000 cancel
            if _action >=511:
                _action -= 511
                if (_action == 0 or _action == 1) and self.actor_color:
                    if _action == 0: return "00"
                    else: return "000"
                if (_action == 2 or _action == 3) and not self.actor_color:
                    if _action == 2: return "00"
                    else: return "000"
                elif _action == 4:
                    return "#"
                else: return "N"
            #pawn transformation
            else:
                #black
                if _action >=256:
                    _action -= 256
                    from_cell = "1" + (str)((_action//(32))%64)
                    to_cell = "0" + (str)((_action//(8))%8)
                    figure = (str)(_action%4 + 1)
                    assert int(from_cell[1])<8 and int(to_cell[1])<8, f'error 2 {action}' 
                    return from_cell + to_cell + (str)(figure)
                else:
                    #white
                    from_cell = "6" + (str)((_action//(32))%64)
                    to_cell = "7" + (str)((_action//(8))%8)
                    figure = (str)(_action%4 + 1)
                    assert int(from_cell[1])<8 and int(to_cell[1])<8, f'error 3 {action}' 
                    return from_cell + to_cell + (str)(figure)
        return self.all_moves[action]

    def opponent_policy(self):
        if self.opponent_type == 0:
            #random move
            rand_move = self.possible_moves[randint(0, len(self.possible_moves)-1)]
            if rand_move.is_pt():
                rand_move.trans_to_figure('1')
            return rand_move
            


    def to_gym_state(self):
        '''
        Преобразует состояние игры(game_state) в сотояние(state) для работы нейронной сети
        Исправить для игры за черных
        '''
        figures = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6} # empty = 0
        game_state = []
        for i in range(8):
            game_state.append([])
            for j in range(8):
                i_j_cell = self.game_state[i][j]
                if i_j_cell:
                    gym_figure = figures[i_j_cell[1]]
                    if (i_j_cell[0] == 'b' and self.current_color) or (i_j_cell[0] == 'w' and  not self.current_color):
                        gym_figure *= -1
                    game_state[i].append(gym_figure)
                else:#empty cell
                    game_state[i].append(0)
        self.state = game_state
    def render(self):
        pass
    def close(self):
        print("close")
        pass

        