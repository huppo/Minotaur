import struct
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import os

def read_wad_file(filename):
    """Чтение WAD файла в бинарном режиме"""
    with open(filename, 'rb') as f:
        return f.read()

def parse_wad_header(data):
    """Парсинг заголовка WAD файла"""
    wad_type = data[:4].decode('ascii')
    num_lumps = struct.unpack('<I', data[4:8])[0]
    info_table_offset = struct.unpack('<I', data[8:12])[0]
    return wad_type, num_lumps, info_table_offset

def find_map_directory(data, map_name):
    """Поиск директории для указанной карты"""
    wad_type, num_lumps, info_table_offset = parse_wad_header(data)
    
    map_found = False
    map_lumps = []
    
    for i in range(num_lumps):
        offset = info_table_offset + i * 16
        lump_offset = struct.unpack('<I', data[offset:offset+4])[0]
        lump_size = struct.unpack('<I', data[offset+4:offset+8])[0]
        lump_name = data[offset+8:offset+16].decode('ascii').rstrip('\0')
        
        if lump_name == map_name:
            map_found = True
            continue
        
        if map_found:
            if lump_name in ['THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SEGS', 
                            'SSECTORS', 'NODES', 'SECTORS', 'REJECT', 'BLOCKMAP']:
                map_lumps.append((lump_name, lump_offset, lump_size))
            else:
                break
    
    # Создаем словарь с информацией о каждом lump'е карты
    lumps_dict = {}
    for lump in map_lumps:
        lumps_dict[lump[0]] = (lump[1], lump[2])
    
    return lumps_dict

def parse_vertexes(data, offset, size):
    """Парсинг вершин карты"""
    vertexes = []
    num_vertexes = size // 4  # Каждая вершина занимает 4 байта (2 int16)
    
    for i in range(num_vertexes):
        v_offset = offset + i * 4
        x = struct.unpack('<h', data[v_offset:v_offset+2])[0]
        y = struct.unpack('<h', data[v_offset+2:v_offset+4])[0]
        vertexes.append((x, y))
    
    return vertexes

def parse_linedefs(data, offset, size):
    """Парсинг линий карты"""
    linedefs = []
    num_linedefs = size // 14  # Каждая линия занимает 14 байт
    
    for i in range(num_linedefs):
        ld_offset = offset + i * 14
        start_vertex = struct.unpack('<H', data[ld_offset:ld_offset+2])[0]
        end_vertex = struct.unpack('<H', data[ld_offset+2:ld_offset+4])[0]
        flags = struct.unpack('<H', data[ld_offset+4:ld_offset+6])[0]
        special_type = struct.unpack('<H', data[ld_offset+6:ld_offset+8])[0]
        sector_tag = struct.unpack('<H', data[ld_offset+8:ld_offset+10])[0]
        front_sidedef = struct.unpack('<H', data[ld_offset+10:ld_offset+12])[0]
        back_sidedef = struct.unpack('<H', data[ld_offset+12:ld_offset+14])[0]
        
        linedefs.append({
            'start_vertex': start_vertex,
            'end_vertex': end_vertex,
            'flags': flags,
            'special_type': special_type,
            'sector_tag': sector_tag,
            'front_sidedef': front_sidedef,
            'back_sidedef': back_sidedef
        })
    
    return linedefs

def draw_map(vertexes, linedefs, output_filename):
    """Рисование карты"""
    fig, ax = plt.subplots(figsize=(20, 20))
    
    # Рисуем все линии
    for line in linedefs:
        start = vertexes[line['start_vertex']]
        end = vertexes[line['end_vertex']]
        
        # Проверяем, является ли линия односторонней (нет back_sidedef)
        if line['back_sidedef'] == 0xFFFF:
            color = 'black'  # Односторонние стены - черные
            linewidth = 1.5
        else:
            color = 'gray'   # Двусторонние стены - серые
            linewidth = 0.5
        
        ax.add_line(mlines.Line2D(
            [start[0], end[0]], 
            [start[1], end[1]], 
            color=color, 
            linewidth=linewidth
        ))
    
    # Настройки графика
    ax.autoscale()
    ax.set_aspect('equal')
    ax.set_title(f'Doom 2 Map: MAP01 (Top View)')
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    
    # Сохраняем в файл
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Map saved to {output_filename}")

def extract_and_draw_map(wad_filename, map_name, output_filename):
    """Основная функция для извлечения и рисования карты"""
    data = read_wad_file(wad_filename)
    map_lumps = find_map_directory(data, map_name)
    
    if not map_lumps:
        print(f"Map {map_name} not found in WAD file")
        return
    
    # Получаем необходимые данные
    if 'VERTEXES' not in map_lumps or 'LINEDEFS' not in map_lumps:
        print("Required map data (VERTEXES or LINEDEFS) not found")
        return
    
    vertexes = parse_vertexes(data, map_lumps['VERTEXES'][0], map_lumps['VERTEXES'][1])
    linedefs = parse_linedefs(data, map_lumps['LINEDEFS'][0], map_lumps['LINEDEFS'][1])
    
    # Рисуем карту
    draw_map(vertexes, linedefs, output_filename)

# Использование
if __name__ == "__main__":
    wad_file = "minotaur.wad"
    output_file = "minotaur_map00.png"
    
    if os.path.exists(wad_file):
        extract_and_draw_map(wad_file, "MAP00", output_file)
    else:
        print(f"Error: File {wad_file} not found")