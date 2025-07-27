# Генератор лабиринта
import random
import sys
import argparse
from datetime import datetime

# Константы
EXIT_FLAG = 16  # Пятый бит для пометки выхода

class MazeGenerator:
    def __init__(self, width=6, height=8):
        self.width = width
        self.height = height
        self.maze = [[15 for _ in range(width)] for _ in range(height)]
        self.generate_maze()

    def generate_maze(self, start_x=0, start_y=0):
        stack = [(start_x, start_y)]
        visited = set(stack)
        
        while stack:
            x, y = stack[-1]
            neighbors = []
            
            # Проверяем соседей
            if x > 0 and (x-1, y) not in visited:
                neighbors.append(('left', x-1, y))
            if y > 0 and (x, y-1) not in visited:
                neighbors.append(('up', x, y-1))
            if x < self.width-1 and (x+1, y) not in visited:
                neighbors.append(('right', x+1, y))
            if y < self.height-1 and (x, y+1) not in visited:
                neighbors.append(('down', x, y+1))
            
            if neighbors:
                direction, nx, ny = random.choice(neighbors)
                
                # Убираем стену между текущей клеткой и соседом
                if direction == 'left':
                    self.maze[y][x] &= ~1  # Убираем левую стену текущей клетки
                    self.maze[ny][nx] &= ~4  # Убираем правую стену соседней
                elif direction == 'up':
                    self.maze[y][x] &= ~2  # Убираем верхнюю стену текущей клетки
                    self.maze[ny][nx] &= ~8  # Убираем нижнюю стену соседней
                elif direction == 'right':
                    self.maze[y][x] &= ~4  # Убираем правую стену текущей клетки
                    self.maze[ny][nx] &= ~1  # Убираем левую стену соседней
                elif direction == 'down':
                    self.maze[y][x] &= ~8  # Убираем нижнюю стену текущей клетки
                    self.maze[ny][nx] &= ~2  # Убираем верхнюю стену соседней
                
                stack.append((nx, ny))
                visited.add((nx, ny))
            else:
                stack.pop()
        
        # Вход (левая нижняя клетка — убираем левую стену)
        self.maze[self.height-1][0] &= ~1
        # Выход (правая верхняя клетка — убираем правую стену и ставим флаг выхода)
        self.maze[0][self.width-1] &= ~4
        self.maze[0][self.width-1] |= EXIT_FLAG
        
        # Закрываем остальные внешние стены
        for y in range(self.height):
            if y != 0:
                self.maze[y][0] |= 1  # Левая стена
            if y != self.height-1:
                self.maze[y][self.width-1] |= 4  # Правая стена
        
        for x in range(self.width):
            if x != self.width-1:
                self.maze[0][x] |= 2  # Верхняя стена
            if x != 0:
                self.maze[self.height-1][x] |= 8  # Нижняя стена

    def save_to_file(self, filename):
        """Сохраняет текущий лабиринт в файл"""
        try:
            with open(filename, 'w') as f:
                f.write(f"{self.width} {self.height}\n")
                for row in self.maze:
                    f.write(" ".join(map(str, row)) + "\n")
            print(f"Лабиринт сохранён в файл: {filename}")
            return True
        except IOError as e:
            print(f"Ошибка при сохранении файла: {e}")
            return False

def main():
    # Настройка парсера аргументов командной строки
    parser = argparse.ArgumentParser(description='Maze Generator')
    parser.add_argument('-o', '--output', required=True, help='Имя файла для сохранения лабиринта')
    parser.add_argument('-w', '--width', type=int, default=6, help='Ширина лабиринта')
    parser.add_argument('-H', '--height', type=int, default=8, help='Высота лабиринта')
    args = parser.parse_args()

    # Создаем генератор лабиринта
    generator = MazeGenerator(args.width, args.height)
    
    # Сохраняем лабиринт в файл
    if not generator.save_to_file(args.output):
        sys.exit(1)

if __name__ == "__main__":
    main()