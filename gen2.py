import struct
import os
import sys
from collections import OrderedDict
import random

class WADGenerator:
    def __init__(self, maze_file=None):
        self.maze_file = maze_file
        
    def parse_maze_file(self):
        """Parse the maze file and return grid and dimensions"""
        if not self.maze_file or not os.path.exists(self.maze_file):
            return None, None, None
            
        with open(self.maze_file, 'r') as f:
            lines = f.readlines()
            
        # First line is dimensions
        width, height = map(int, lines[0].strip().split())
        grid = []
        
        for line in lines[1:]:
            row = list(map(int, line.strip().split()))
            grid.append(row)
            
        return width, height, grid
    
    def create_maze_geometry(self, width, height, grid):
        """Create vertices, linedefs and sidedefs based on maze grid"""
        cell_size = 128  # Size of each cell in map units
        vertices = []
        linedefs = []
        sidedefs = []
        
        # First, create all the vertices for each cell corner
        vertex_grid = []
        for y in range(height + 1):
            row = []
            for x in range(width + 1):
                vertex_x = x * cell_size
                vertex_y = y * cell_size
                vertices.append((vertex_x, vertex_y))
                row.append(len(vertices) - 1)
            vertex_grid.append(row)
        
        # Now create walls based on cell data
        for y in range(height):
            for x in range(width):
                cell = grid[y][x]
                
                # Check each bit for walls (assuming bits represent walls in N, E, S, W order)
                # Bottom
                if cell & 0b0010:
                    v1 = vertex_grid[y][x]
                    v2 = vertex_grid[y][x+1]
                    linedefs.append((v1, v2, 1, 0, 0, 0, 0xFFFF))
                
                # Right
                if cell & 0b0100:
                    v1 = vertex_grid[y][x+1]
                    v2 = vertex_grid[y+1][x+1]
                    linedefs.append((v1, v2, 1, 0, 0, 0, 0xFFFF))
                
                # Top
                if cell & 0b1000:
                    v1 = vertex_grid[y+1][x+1]
                    v2 = vertex_grid[y+1][x]
                    linedefs.append((v1, v2, 1, 0, 0, 0, 0xFFFF))
                
                # Left
                if cell & 0b0001:
                    v1 = vertex_grid[y+1][x]
                    v2 = vertex_grid[y][x]
                    linedefs.append((v1, v2, 1, 0, 0, 0, 0xFFFF))
        
        return vertices, linedefs, sidedefs
    
    def create_simple_blockmap(self, vertices, width, height):
        """Create a minimal blockmap"""
        # Blockmap header
        origin_x = min(v[0] for v in vertices)
        origin_y = min(v[1] for v in vertices)
        blocks_x = (width // 128) + 1
        blocks_y = (height // 128) + 1
        
        data = bytearray()
        data += struct.pack('<hh', origin_x, origin_y)
        data += struct.pack('<hh', blocks_x, blocks_y)
        
        # Empty blocklist (all blocks empty)
        for _ in range(blocks_x * blocks_y):
            data += struct.pack('<h', 0)  # 0 = no linedefs
        data += struct.pack('<h', -1)    # End of blocklist marker
        
        return bytes(data)

    def create_simple_map(self):
        """Create a simple map with monsters, items and exit"""
        # Try to parse maze file first
        maze_width, maze_height, grid = self.parse_maze_file()
        block = 128
        if grid:
            # Create maze geometry
            vertices_, linedefs_, sidedefs_ = self.create_maze_geometry(maze_width, maze_height, grid)
            map_width = maze_width * block
            map_height = maze_height * block
        else:
            vertices_ = []
            linedefs_ = []
            map_width = 8 * block
            map_height = 10 * block

        # Outer boundary vertices
        n = len(vertices_)  # Start index for boundary linedefs
        print(f"{n}")
        line = 1
        vertices = [
            (line+0, map_height-line),     # 0
            (map_width-line, map_height-line), # 1
            (map_width-line, line+0),     # 2
            (line+0, line+0),         # 3
        ]
        
        vertices = vertices_ + vertices
        #vertices = vertices_ 
        #vertices = []

        vertices.append((line+line+0, line+line+0))  # Exit
        vertices.append((line+line+0, line+line+block))  # Exit
        

        # Outer boundary linedefs
        
        linedefs = [
            # start, end, flags, special, tag, front, back
            (n+0, n+1, 1, 0, 0, 0, 0xFFFF),  # Bottom wall
            (n+1, n+2, 1, 0, 0, 0, 0xFFFF),  # Right wall
            (n+2, n+3, 1, 0, 0, 0, 0xFFFF),  # Top wall (exit)(n+2, n+3, 5, 11, 666, 0, 0xFFFF),  # Top wall (exit)
            (n+3, n+0, 1, 0, 0, 0, 0xFFFF),    # Left wall
        ]
        
        linedefs = linedefs_ + linedefs
        #linedefs = linedefs_
        #linedefs=[]
        linedefs.append((n+4, n+5, 5, 11, 666, 1, 0xFFFF))  # Top wall (exit)  # Exit
        
        # Sidedefs
        sidedefs = [
            (0, 0, "STARGR2", "STARGR2", "STARGR2", 0),
            (0, 0, "SW2STONE", "SW2STONE", "SW2STONE", 0),
            
        ]
        
        wall_height = 128
        
        # Sectors
        sectors = [
            (0, wall_height, "SKY1", "FLAT5_1", 192, 0, 0),  # Main area
            (0, wall_height, "MFLR8_1", "MFLR8_1", 250, 0, 0),  # Inner area
        ]
        
        # Things - position them randomly in the maze cells
        things = [
            # Player start (random position)
            (int(random.randint(0, maze_width-1)*block+block/2), 
             int(random.randint(0, maze_height-1)*block+block/2), 
             90, 1, 7),
            
            # Exit switch (place it near the edge)
            (int(map_width - block/2), int(map_height - block/2), 0, 11, 7)
        ]

        # Add random monsters
        for _ in range(random.randint(6, 8)):
            things.append((
                int(random.randint(0, maze_width-1)*block+block/2), 
                int(random.randint(0, maze_height-1)*block+block/2), 
                0, 3004, 7))  # Imp

        # Add random ammo boxes
        for _ in range(random.randint(6, 8)):
            things.append((
                int(random.randint(0, maze_width-1)*block+block/2), 
                int(random.randint(0, maze_height-1)*block+block/2), 
                0, 2048, 7))  # Ammo box
        
        # Blockmap
        blockmap = self.create_simple_blockmap(vertices, map_width, map_height)
        
        return {
            'THINGS': self.pack_things(things),
            'LINEDEFS': self.pack_linedefs(linedefs),
            'SIDEDEFS': self.pack_sidedefs(sidedefs),
            'VERTEXES': self.pack_vertexes(vertices),
            'SECTORS': self.pack_sectors(sectors),
            'BLOCKMAP': blockmap
        }
    
    def pack_things(self, things):
        """Pack things data into binary format"""
        data = bytearray()
        for thing in things:
            data += struct.pack('<hhhhH', *thing)
        return bytes(data)
    
    def pack_linedefs(self, linedefs):
        """Pack linedefs data into binary format"""
        data = bytearray()
        for ld in linedefs:
            data += struct.pack('<HHHHHHH', *ld)
        return bytes(data)
    
    def pack_sidedefs(self, sidedefs):
        """Pack sidedefs data into binary format"""
        data = bytearray()
        for sd in sidedefs:
            upper = sd[2].ljust(8, '\0').encode('ascii')
            lower = sd[3].ljust(8, '\0').encode('ascii')
            middle = sd[4].ljust(8, '\0').encode('ascii')
            data += struct.pack('<hh', sd[0], sd[1])
            data += upper + lower + middle
            data += struct.pack('<h', sd[5])
        return bytes(data)
    
    def pack_vertexes(self, vertexes):
        """Pack vertexes data into binary format"""
        data = bytearray()
        for v in vertexes:
            data += struct.pack('<hh', v[0], v[1])
        return bytes(data)
    
    def pack_sectors(self, sectors):
        """Pack sectors data into binary format"""
        data = bytearray()
        for sec in sectors:
            floor_tex = sec[2].ljust(8, '\0').encode('ascii')
            ceil_tex = sec[3].ljust(8, '\0').encode('ascii')
            data += struct.pack('<hh', sec[0], sec[1])
            data += floor_tex + ceil_tex
            data += struct.pack('<hHH', sec[4], sec[5], sec[6])
        return bytes(data)
    
    def create_new_wad(self, output_file):
        """Create a new WAD file with MAP00"""
        # Start building the new WAD
        new_wad = bytearray()
        directory = []
        offset = 12  # Start after header
        
        # Add WAD header placeholder
        new_wad.extend(b'PWAD')  # We're creating a PWAD (patch WAD)
        new_wad.extend(b'\0\0\0\0')  # Placeholder for num lumps
        new_wad.extend(b'\0\0\0\0')  # Placeholder for directory offset
        
        # Create and add our new MAP00
        map_data = self.create_simple_map()
        
        # Add MAP00 marker
        map00_marker = b'MAP00\0\0\0'
        new_wad.extend(map00_marker)
        directory.append({
            'name': 'MAP00',
            'offset': offset,
            'size': len(map00_marker)
        })
        offset += len(map00_marker)
        
        # Add all map lumps
        lump_order = ['THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SECTORS', 'BLOCKMAP']
        for lump_name in lump_order:
            lump_data = map_data[lump_name]
            new_wad.extend(lump_data)
            directory.append({
                'name': lump_name,
                'offset': offset,
                'size': len(lump_data)
            })
            offset += len(lump_data)
        
        # Now write the directory
        dir_offset = len(new_wad)
        for entry in directory:
            # Write directory entry
            new_wad.extend(struct.pack('<II', entry['offset'], entry['size']))
            name = entry['name'].ljust(8, '\0').encode('ascii')
            new_wad.extend(name)
        
        # Update header with correct values
        new_wad[4:8] = struct.pack('<I', len(directory))
        new_wad[8:12] = struct.pack('<I', dir_offset)
        
        # Write the new WAD file
        with open(output_file, 'wb') as f:
            f.write(new_wad)
        
        print(f"Successfully created {output_file} with {len(directory)} lumps")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py output.wad [maze_file.txt]")
        return
    
    output_wad = sys.argv[1]
    maze_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("Creating new WAD with MAP00...")
    generator = WADGenerator(maze_file)
    generator.create_new_wad(output_wad)
    
    print("Done!")

if __name__ == "__main__":
    main()