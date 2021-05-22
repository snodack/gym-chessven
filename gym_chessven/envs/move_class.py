#Классы для ходов #7
#Создать класс, в котором будет учитываться начальное поле и конечное поле и куда необходимо нажать 
# для этого ходп(пригодиться для рокировки и апргейда пешек). Также там можно иметь функцию преобразования 
# в книжный вид для отображения истории игры

file_table = {
    '0': '8',
    '1': '7',
    '2': '6',
    '3': '5',
    '4': '4',
    '5': '3',
    '6': '2',
    '7': '1',
}
rank_table = {
    '0': 'a',
    '1': 'b',
    '2': 'c',
    '3': 'd',
    '4': 'e',
    '5': 'f',
    '6': 'g',
    '7': 'h',
}
class CMove:
    def __init__(self, player_color, file_rank_from, file_rank_to = None, pawn_transformation = False, aisle = False):
        self.cell_from = file_rank_from
        self.cell_to = file_rank_to
        self.player_color = player_color
        self.pawn_transformation = pawn_transformation 
        self.aisle = aisle
        self.trans_to = ''
    def get_from(self):
        '''
        Возвращает координаты клетки откуда начинается ход
        '''
        #Не рокировка
        if self.cell_to != None:
            return self.cell_from
        else:
            return (str)(7-7*(not self.player_color)) + '4'
    
    def get_to_int(self):
        '''
        Возвращает координаты клетки куда необходимо нажать чтобы совершить ход в значении (int, int)
        '''
        return ((int)(self.cell_to[0]), (int)(self.cell_to[1]))

    def get_to(self):
        '''
        Возвращает координаты клетки куда необходимо нажать чтобы совершить ход
        '''
        #Не рокировка
        if self.cell_to != None:
            return self.cell_to 
        #Длинная
        elif len(self.cell_from) > 2:
            return (str)(7-7*(not self.player_color)) + '2'
        #Короткая
        else:
            return (str)(7-7*(not self.player_color)) + '6'

    def get_move(self):
        '''
        Возвращает ход в математическом типе
        '''
        if self.cell_to == None:
            return self.cell_from
        else:
            return self.cell_from + self.cell_to + self.trans_to

    def is_pt(self):
        '''
        Является ли ход трансормацией в другую фигуру?
        '''
        return self.pawn_transformation
    
    def trans_to_figure(self, figure):
        '''
        Полностью преобразует ход в трансформацию в другую фигуру
        '''
        self.trans_to = figure
    
    def get_player_color(self):
        '''
        Возвращает цвет игрока сделавшего ход
        '''
        return self.player_color
    def get_allow_aisle(self):
        '''
        Возвращает значение - можно ли после этого хода совершить взятие на проходе
        '''
        return self.aisle
    def get_def_format(self):
        if self.cell_to!= None:
            def_format = rank_table[self.cell_to[1]] + file_table[self.cell_to[0]]+\
                rank_table[self.cell_to[3]] + file_table[self.cell_to[2]]
        else:
            return self.cell_from 
    #Функцию превращения сюда
