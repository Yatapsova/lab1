import sys
import pygame
from typing import List, Tuple

# Инициализация Pygame
pygame.init()

# Константы
CELL_SIZE = 50
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# Символы карты
WALL = '1'
EMPTY = '0'
PLAYER = 'P'
COLLECTIBLE = 'C'
EXIT = 'E'

class Game:
    def _init_(self, map_data: List[str]):
        self.map_data = [list(row) for row in map_data]
        self.original_map = [list(row) for row in map_data]
        self.moves = 0
        self.collected = 0
        self.total_collectibles = 0
        self.game_over = False
        self.win = False
        
        # Находим игрока и считаем коллекционные предметы
        self.player_pos = self.find_player()
        self.count_collectibles()
        
        # Размеры окна
        self.width = len(self.map_data[0]) * CELL_SIZE
        self.height = len(self.map_data) * CELL_SIZE
        
        # Создание окна
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("2D Game - Required Part")
        
        # Шрифт для отображения текста (будет инициализирован позже)
        self.font = None
        self.init_font()
        
        # Часы для контроля FPS
        self.clock = pygame.time.Clock()
    
    def init_font(self):
        """Инициализация шрифта"""
        try:
            self.font = pygame.font.Font(None, 36)
        except:
            # Запасной вариант, если основной шрифт не доступен
            self.font = pygame.font.SysFont('arial', 36)
    
    def find_player(self) -> Tuple[int, int]:
        """Находит начальную позицию игрока на карте"""
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                if cell == PLAYER:
                    return (x, y)
        return (1, 1)  # Позиция по умолчанию
    
    def count_collectibles(self):
        """Считает общее количество коллекционных предметов"""
        self.total_collectibles = sum(
            row.count(COLLECTIBLE) for row in self.map_data
        )
    
    def draw(self):
        """Отрисовка игры"""
        self.screen.fill(BLACK)
        
        # Отрисовка карты
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, 
                                 CELL_SIZE, CELL_SIZE)
                
                if cell == WALL:
                    pygame.draw.rect(self.screen, GRAY, rect)
                    pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)
                elif cell == EMPTY:
                    pygame.draw.rect(self.screen, BLACK, rect)
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                elif cell == COLLECTIBLE:
                    pygame.draw.rect(self.screen, BLACK, rect)
                    pygame.draw.circle(self.screen, YELLOW, 
                                     (x * CELL_SIZE + CELL_SIZE // 2,
                                      y * CELL_SIZE + CELL_SIZE // 2),
                                     CELL_SIZE // 4)
                elif cell == EXIT:
                    pygame.draw.rect(self.screen, GREEN, rect)
                    pygame.draw.rect(self.screen, (0, 200, 0), rect, 3)
                    # Рисуем букву E
                    text = self.font.render('E', True, BLACK)
                    text_rect = text.get_rect(center=rect.center)
                    self.screen.blit(text, text_rect)
        
        # Отрисовка игрока
        player_rect = pygame.Rect(
            self.player_pos[0] * CELL_SIZE + 5,
            self.player_pos[1] * CELL_SIZE + 5,
            CELL_SIZE - 10,
            CELL_SIZE - 10
        )
        pygame.draw.rect(self.screen, BLUE, player_rect)
        
        # Отрисовка информации о ходе игры
        info_text = f"Moves: {self.moves}  Collected: {self.collected}/{self.total_collectibles}"
        text_surface = self.font.render(info_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))
        
        # Сообщение о победе
        if self.win:
            win_text = "YOU WIN! Press ESC to exit"
            win_surface = self.font.render(win_text, True, GREEN)
            win_rect = win_surface.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(win_surface, win_rect)
        
        pygame.display.flip()
    
    def move_player(self, dx: int, dy: int):
        """Перемещение игрока"""
        if self.game_over or self.win:
            return
        
        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy
        
        # Проверка границ карты
        if (0 <= new_x < len(self.map_data[0]) and 
            0 <= new_y < len(self.map_data)):
            
            target_cell = self.map_data[new_y][new_x]
            
            # Проверка на стену
            if target_cell == WALL:
                return
            
            # Проверка на коллекционный предмет
            if target_cell == COLLECTIBLE:
                self.collected += 1
                self.map_data[new_y][new_x] = EMPTY
            
            # Проверка на выход
            if target_cell == EXIT:
                if self.collected >= self.total_collectibles:
                    self.win = True
                else:
                    # Нельзя выйти пока не собраны все предметы
                    return
            
            # Перемещение игрока
            self.map_data[y][x] = EMPTY
            self.player_pos = (new_x, new_y)
            self.map_data[new_y][new_x] = PLAYER
            self.moves += 1
            
            # Вывод в консоль (обязательное требование)
            print(f"Move {self.moves}: Player at ({new_x}, {new_y})")
    
    def run(self):
        """Основной игровой цикл"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    # Управление игроком
                    if not self.game_over and not self.win:
                        if event.key == pygame.K_w or event.key == pygame.K_UP:
                            self.move_player(0, -1)
                        elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                            self.move_player(0, 1)
                        elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                            self.move_player(-1, 0)
                        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                            self.move_player(1, 0)
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

def main():
    """Основная функция"""
    # Карта из задания
    game_map = [
        "1111111111111",
        "1001000000001",
        "1000011111001",
        "1P0011E0000C1",
        "1111111111111"
    ]
    
    # Альтернативная, более интересная карта
    alternative_map = [
        "111111111111111",
        "1C0000000000001",
        "101111011110101",
        "100P00010000001",
        "101111011111101",
        "1000C0100000001",
        "101111011111101",
        "10000001E0000C1",
        "111111111111111"
    ]
    
    print("Starting 2D Game - Required Part")
    print("Controls: W/A/S/D or Arrow Keys to move")
    print("Collect all yellow items (C) before exiting through green exit (E)")
    print("Press ESC to quit\n")
    
    game = Game(alternative_map)  # Можно заменить на game_map
    game.run()

if _name_ == "_main_":
    main()