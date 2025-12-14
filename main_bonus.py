import sys
import pygame
import random
from typing import List, Tuple, Optional
from enum import Enum
import os

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
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 255)

# Символы карты
WALL = '1'
EMPTY = '0'
PLAYER = 'P'
COLLECTIBLE = 'C'
EXIT = 'E'
PATROL = 'X'

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Patrol:
    def _init_(self, x: int, y: int, patrol_route: List[Tuple[int, int]] = None):
        self.x = x
        self.y = y
        self.direction = Direction.RIGHT
        self.move_counter = 0
        self.move_delay = 15  # Замедление движения патруля
        self.animation_frame = 0
        self.animation_speed = 5
        
        # Маршрут патрулирования
        if patrol_route:
            self.patrol_route = patrol_route
            self.route_index = 0
        else:
            self.patrol_route = None
    
    def move(self, game_map: List[List[str]]):
        """Движение патруля"""
        self.move_counter += 1
        if self.move_counter < self.move_delay:
            return
        
        self.move_counter = 0
        
        # Анимация
        self.animation_frame = (self.animation_frame + 1) % (self.animation_speed * 4)
        
        # Если есть маршрут - следовать ему
        if self.patrol_route:
            target = self.patrol_route[self.route_index]
            dx = target[0] - self.x
            dy = target[1] - self.y
            
            # Движение к следующей точке маршрута
            if dx != 0:
                new_x = self.x + (1 if dx > 0 else -1)
                if (0 <= new_x < len(game_map[0]) and 
                    game_map[self.y][new_x] != WALL):
                    self.x = new_x
            elif dy != 0:
                new_y = self.y + (1 if dy > 0 else -1)
                if (0 <= new_y < len(game_map) and 
                    game_map[new_y][self.x] != WALL):
                    self.y = new_y
            
            # Если достигли точки маршрута, переходим к следующей
            if self.x == target[0] and self.y == target[1]:
                self.route_index = (self.route_index + 1) % len(self.patrol_route)
        
        else:
            # Случайное движение
            directions = list(Direction)
            random.shuffle(directions)
            
            for direction in directions:
                dx, dy = direction.value
                new_x, new_y = self.x + dx, self.y + dy
                
                if (0 <= new_x < len(game_map[0]) and 
                    0 <= new_y < len(game_map) and 
                    game_map[new_y][new_x] != WALL):
                    
                    self.x = new_x
                    self.y = new_y
                    self.direction = direction
                    break
    
    def draw(self, screen, cell_size: int):
        """Отрисовка патруля с анимацией"""
        rect = pygame.Rect(
            self.x * cell_size + 5,
            self.y * cell_size + 5,
            cell_size - 10,
            cell_size - 10
        )
        
        # Простая анимация изменения цвета
        pulse = abs((self.animation_frame % (self.animation_speed * 2)) - self.animation_speed) / self.animation_speed
        color = (
            int(255 * (0.7 + 0.3 * pulse)),
            int(165 * (0.7 + 0.3 * pulse)),
            0
        )
        
        pygame.draw.rect(screen, color, rect)
        
        # Глаза патруля (направление взгляда)
        eye_size = cell_size // 8
        eye_offset = cell_size // 4
        
        if self.direction == Direction.RIGHT:
            eye_pos = (rect.right - eye_offset, rect.centery)
        elif self.direction == Direction.LEFT:
            eye_pos = (rect.left + eye_offset, rect.centery)
        elif self.direction == Direction.UP:
            eye_pos = (rect.centerx, rect.top + eye_offset)
        else:  # DOWN
            eye_pos = (rect.centerx, rect.bottom - eye_offset)
        
        pygame.draw.circle(screen, WHITE, eye_pos, eye_size)
        pygame.draw.circle(screen, BLACK, eye_pos, eye_size // 2)

class BonusGame:
    def _init_(self, map_data: List[str]):
        self.map_data = [list(row) for row in map_data]
        self.original_map = [list(row) for row in map_data]
        self.moves = 0
        self.collected = 0
        self.total_collectibles = 0
        self.game_over = False
        self.win = False
        self.lose = False
        
        # Находим игрока и считаем коллекционные предметы
        self.player_pos = self.find_player()
        self.count_collectibles()
        
        # Инициализация патрулей
        self.patrols = self.init_patrols()
        
        # Анимация игрока
        self.player_animation_frame = 0
        self.player_animation_speed = 8
        
        # Размеры окна
        self.width = len(self.map_data[0]) * CELL_SIZE
        self.height = len(self.map_data) * CELL_SIZE + 50  # Дополнительное место для HUD
        
        # Создание окна
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("2D Game - Bonus Part")
        
        # Шрифты
        self.font_large = None
        self.font_medium = None
        self.init_fonts()
        
        # Загрузка спрайтов (если есть)
        self.sprites = self.load_sprites()
        
        # Часы для контроля FPS
        self.clock = pygame.time.Clock()
    
    def init_fonts(self):
        """Инициализация шрифтов"""
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
        except:
            self.font_large = pygame.font.SysFont('arial', 48)
            self.font_medium = pygame.font.SysFont('arial', 36)
    
    def load_sprites(self):
        """Загрузка спрайтов (если файлы существуют)"""
        sprites = {}
        sprite_files = {
            'player': 'player.png',
            'wall': 'wall.png',
            'collectible': 'collectible.png',
            'exit': 'exit.png',
            'patrol': 'patrol.png',
            'floor': 'floor.png'
        }
        
        for key, filename in sprite_files.items():
            path = os.path.join('assets', filename)
            if os.path.exists(path):
                try:
                    sprite = pygame.image.load(path)
                    sprite = pygame.transform.scale(sprite, (CELL_SIZE, CELL_SIZE))
                    sprites[key] = sprite
                except:
                    print(f"Could not load sprite: {filename}")
        
        return sprites if sprites else None
    
    def find_player(self) -> Tuple[int, int]:
        """Находит начальную позицию игрока на карте"""
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                if cell == PLAYER:
                    return (x, y)
        return (1, 1)
    
    def count_collectibles(self):
        """Считает общее количество коллекционных предметов"""
        self.total_collectibles = sum(
            row.count(COLLECTIBLE) for row in self.map_data
        )
    
    def init_patrols(self) -> List[Patrol]:
        """Инициализация патрулей"""
        patrols = []
        patrol_positions = []
        
        # Находим все позиции патрулей
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                if cell == PATROL:
                    patrol_positions.append((x, y))
        
        # Создаем патрули с маршрутами
        for x, y in patrol_positions:
            # Создаем простой маршрут патрулирования (влево-вправо или вверх-вниз)
            route = []
            
            # Проверяем возможные направления движения
            directions_to_check = [
                [(x-2, y), (x-1, y), (x, y), (x+1, y), (x+2, y)],  # Горизонтальный
                [(x, y-2), (x, y-1), (x, y), (x, y+1), (x, y+2)]   # Вертикальный
            ]
            
            for route_candidate in directions_to_check:
                valid_route = True
                for rx, ry in route_candidate:
                    if (0 <= rx < len(self.map_data[0]) and 
                        0 <= ry < len(self.map_data) and 
                        self.map_data[ry][rx] != WALL):
                        route.append((rx, ry))
                    else:
                        valid_route = False
                        route = []
                        break
                
                if valid_route and len(route) >= 3:
                    break
            
            # Если не нашли хороший маршрут, используем случайное движение
            if len(route) < 3:
                route = None
            
            patrol = Patrol(x, y, route)
            patrols.append(patrol)
        
        return patrols
    
    def draw_hud(self):
        """Отрисовка HUD (количество ходов на экране)"""
        hud_rect = pygame.Rect(0, len(self.map_data) * CELL_SIZE, self.width, 50)
        pygame.draw.rect(self.screen, (40, 40, 40), hud_rect)
        
        # Отображение количества ходов
        moves_text = f"Moves: {self.moves}"
        moves_surface = self.font_medium.render(moves_text, True, WHITE)
        self.screen.blit(moves_surface, (10, len(self.map_data) * CELL_SIZE + 10))
        
        # Отображение собранных предметов
        collect_text = f"Collected: {self.collected}/{self.total_collectibles}"
        collect_surface = self.font_medium.render(collect_text, True, YELLOW)
        self.screen.blit(collect_surface, (200, len(self.map_data) * CELL_SIZE + 10))
        
        # Отображение предупреждения о патрулях
        if self.patrols:
            patrol_text = f"Patrols: {len(self.patrols)} - AVOID THEM!"
            patrol_surface = self.font_medium.render(patrol_text, True, RED)
            self.screen.blit(patrol_surface, (self.width - 300, len(self.map_data) * CELL_SIZE + 10))
    
    def draw(self):
        """Отрисовка игры"""
        self.screen.fill(BLACK)
        
        # Отрисовка карты
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, 
                                 CELL_SIZE, CELL_SIZE)
                
                # Использование спрайтов если они есть
                if self.sprites:
                    if cell == WALL and 'wall' in self.sprites:
                        self.screen.blit(self.sprites['wall'], rect)
                    elif cell == EMPTY and 'floor' in self.sprites:
                        self.screen.blit(self.sprites['floor'], rect)
                    else:
                        # Рисуем стандартными цветами если нет спрайта
                        if cell == WALL:
                            pygame.draw.rect(self.screen, GRAY, rect)
                            pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)
                        elif cell == EMPTY:
                            pygame.draw.rect(self.screen, (30, 30, 30), rect)
                            pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                else:
                    # Рисуем стандартными цветами
                    if cell == WALL:
                        pygame.draw.rect(self.screen, GRAY, rect)
                        pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)
                    elif cell == EMPTY:
                        pygame.draw.rect(self.screen, (30, 30, 30), rect)
                        pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                
                # Коллекционные предметы
                if cell == COLLECTIBLE:
                    if self.sprites and 'collectible' in self.sprites:
                        self.screen.blit(self.sprites['collectible'], rect)
                    else:
                        pygame.draw.rect(self.screen, BLACK, rect)
                        # Анимация вращения
                        angle = pygame.time.get_ticks() // 30 % 360
                        radius = CELL_SIZE // 3
                        center_x = x * CELL_SIZE + CELL_SIZE // 2
                        center_y = y * CELL_SIZE + CELL_SIZE // 2
                        
                        # Вращающийся треугольник
                        points = []
                        for i in range(3):
                            point_angle = angle + i * 120
                            px = center_x + radius * pygame.math.Vector2(1, 0).rotate(point_angle).x
                            py = center_y + radius * pygame.math.Vector2(1, 0).rotate(point_angle).y
                            points.append((px, py))
                        
                        pygame.draw.polygon(self.screen, YELLOW, points)
                
                # Выход
                elif cell == EXIT:
                    if self.sprites and 'exit' in self.sprites:
                        self.screen.blit(self.sprites['exit'], rect)
                    else:
                        # Пульсирующий выход
                        pulse = (pygame.time.get_ticks() % 1000) / 1000
                        pulse_intensity = 0.5 + 0.5 * abs(pulse - 0.5) * 2
                        color = (
                            int(0 * pulse_intensity),
                            int(255 * pulse_intensity),
                            int(0 * pulse_intensity)
                        )
                        pygame.draw.rect(self.screen, color, rect)
                        pygame.draw.rect(self.screen, (0, 200, 0), rect, 3)
                        
                        # Рисуем букву E
                        text = self.font_medium.render('E', True, BLACK)
                        text_rect = text.get_rect(center=rect.center)
                        self.screen.blit(text, text_rect)
        
        # Отрисовка патрулей
        for patrol in self.patrols:
            patrol.draw(self.screen, CELL_SIZE)
        
        # Отрисовка игрока с анимацией
        self.player_animation_frame = (self.player_animation_frame + 1) % (self.player_animation_speed * 4)
        player_rect = pygame.Rect(
            self.player_pos[0] * CELL_SIZE + 5,
            self.player_pos[1] * CELL_SIZE + 5,
            CELL_SIZE - 10,
            CELL_SIZE - 10
        )
        
        if self.sprites and 'player' in self.sprites:
            # Анимация изменения размера
            scale = 1.0 + 0.1 * abs((self.player_animation_frame % (self.player_animation_speed * 2)) 
                                   - self.player_animation_speed) / self.player_animation_speed
            scaled_sprite = pygame.transform.scale(
                self.sprites['player'],
                (int(CELL_SIZE * scale) - 10, int(CELL_SIZE * scale) - 10)
            )
            sprite_rect = scaled_sprite.get_rect(center=player_rect.center)
            self.screen.blit(scaled_sprite, sprite_rect)
        else:
            # Анимация пульсации цвета
            pulse = abs((self.player_animation_frame % (self.player_animation_speed * 2)) 
                       - self.player_animation_speed) / self.player_animation_speed
            color = (
                int(0 * (0.7 + 0.3 * pulse)),
                int(120 * (0.7 + 0.3 * pulse)),
                int(255 * (0.7 + 0.3 * pulse))
            )
            pygame.draw.rect(self.screen, color, player_rect)
            
            # Глаза игрока
            eye_size = CELL_SIZE // 10
            pygame.draw.circle(self.screen, WHITE, 
                             (player_rect.centerx - 10, player_rect.centery - 5), 
                             eye_size)
            pygame.draw.circle(self.screen, WHITE, 
                             (player_rect.centerx + 10, player_rect.centery - 5), 
                             eye_size)
            pygame.draw.circle(self.screen, BLACK, 
                             (player_rect.centerx - 10, player_rect.centery - 5), 
                             eye_size // 2)
            pygame.draw.circle(self.screen, BLACK, 
                             (player_rect.centerx + 10, player_rect.centery - 5), 
                             eye_size // 2)
        
        # Отрисовка HUD
        self.draw_hud()
        
        # Сообщения о победе/проигрыше
        if self.win:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            win_text = "VICTORY! You escaped!"
            win_surface = self.font_large.render(win_text, True, GREEN)
            win_rect = win_surface.get_rect(center=(self.width // 2, self.height // 2 - 50))
            self.screen.blit(win_surface, win_rect)
            
            moves_text = f"Total moves: {self.moves}"
            moves_surface = self.font_medium.render(moves_text, True, WHITE)
            moves_rect = moves_surface.get_rect(center=(self.width // 2, self.height // 2 + 10))
            self.screen.blit(moves_surface, moves_rect)
            
            esc_text = "Press ESC to exit"
            esc_surface = self.font_medium.render(esc_text, True, YELLOW)
            esc_rect = esc_surface.get_rect(center=(self.width // 2, self.height // 2 + 50))
            self.screen.blit(esc_surface, esc_rect)
        
        elif self.lose:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            lose_text = "GAME OVER! Caught by patrol!"
            lose_surface = self.font_large.render(lose_text, True, RED)
            lose_rect = lose_surface.get_rect(center=(self.width // 2, self.height // 2 - 50))
            self.screen.blit(lose_surface, lose_rect)
            
            moves_text = f"Moves survived: {self.moves}"
            moves_surface = self.font_medium.render(moves_text, True, WHITE)
            moves_rect = moves_surface.get_rect(center=(self.width // 2, self.height // 2 + 10))
            self.screen.blit(moves_surface, moves_rect)
            
            esc_text = "Press ESC to exit"
            esc_surface = self.font_medium.render(esc_text, True, YELLOW)
            esc_rect = esc_surface.get_rect(center=(self.width // 2, self.height // 2 + 50))
            self.screen.blit(esc_surface, esc_rect)
        
        pygame.display.flip()
    
    def check_patrol_collision(self) -> bool:
        """Проверка столкновения с патрулями"""
        for patrol in self.patrols:
            if (self.player_pos[0] == patrol.x and 
                self.player_pos[1] == patrol.y):
                return True
        return False
    
    def move_player(self, dx: int, dy: int):
        """Перемещение игрока"""
        if self.game_over or self.win or self.lose:
            return
        
        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy
        
        # Обновление анимации
        self.player_animation_frame = (self.player_animation_frame + 1) % (self.player_animation_speed * 4)
        
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
            
            # Проверка столкновения с патрулями после движения
            if self.check_patrol_collision():
                self.lose = True
                print(f"Game Over! Caught by patrol after {self.moves} moves!")
            else:
                print(f"Move {self.moves}: Player at ({new_x}, {new_y})")
    
    def update_patrols(self):
        """Обновление позиций патрулей"""
        for patrol in self.patrols:
            patrol.move(self.map_data)
        
        # Проверка столкновения после движения патрулей
        if not self.win and not self.lose and self.check_patrol_collision():
            self.lose = True
            print(f"Game Over! Patrol caught you after {self.moves} moves!")
    
    def run(self):
        """Основной игровой цикл"""
        running = True
        patrol_update_counter = 0
        patrol_update_delay = 2  # Патрули двигаются медленнее чем игрок
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    # Управление игроком
                    if not self.game_over and not self.win and not self.lose:
                        if event.key == pygame.K_w or event.key == pygame.K_UP:
                            self.move_player(0, -1)
                        elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                            self.move_player(0, 1)
                        elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                            self.move_player(-1, 0)
                        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                            self.move_player(1, 0)
            
            # Обновление патрулей (двигаются реже чем отрисовывается кадр)
            patrol_update_counter += 1
            if patrol_update_counter >= patrol_update_delay and not self.win and not self.lose:
                self.update_patrols()
                patrol_update_counter = 0
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

def main():
    """Основная функция"""
    # Карта с патрулями для бонусной части
    bonus_map = [
        "111111111111111",
        "1C0000000X00001",
        "101111011110101",
        "100P00010000001",
        "101111011111101",
        "1000C01000X0001",
        "101111011111101",
        "10000001E0000C1",
        "111111111111111"
    ]
    
    # Другая карта с патрулями
    alternative_bonus_map = [
        "11111111111111111",
        "1C0001000100010C1",
        "10101010101010101",
        "1P00X010001000X01",
        "11111111111111111",
        "1000000C000000001",
        "10111011101110101",
        "10001000100010001",
        "11101110111011111",
        "1C0100010001000C1",
        "10111011101110101",
        "1000X000E0000X001",
        "11111111111111111"
    ]
    
    print("Starting 2D Game - Bonus Part")
    print("Controls: W/A/S/D or Arrow Keys to move")
    print("Collect all items (C) before exiting through green exit (E)")
    print("Avoid patrols (X) - they will catch you!")
    print("Press ESC to quit\n")
    
    game = BonusGame(alternative_bonus_map)  # Можно заменить на bonus_map
    game.run()

if _name_ == "_main_":
    main()