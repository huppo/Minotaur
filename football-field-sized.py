import struct
import os
from collections import OrderedDict

class WADProcessor:
    def __init__(self):
        self.data = b''
        self.header = {}
        self.directory = OrderedDict()
        
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
        width = 1024*10
        height = 1024*10
        wall_height = 128*10
        block=32
        
        # Vertices
        vertices = [
            (block, height-block),         # 0
            (width-block, height-block),     # 1
            (width-block, block), # 2
            (block, block)     # 3
        ]
        
        # Linedefs - добавим выходную линию с special type
        linedefs = [
            # start, end, flags, special, tag, front, back
            (0, 1, 1, 0, 0, 0, 0xFFFF),  # Bottom wall
            (1, 2, 1, 0, 0, 0, 0xFFFF),   # Right wall
            (2, 3, 1, 0, 0, 0, 0xFFFF),  # Top wall (exit)
            (3, 0, 1, 0, 0, 0, 0xFFFF),    # Left wall
        ]
        
        # Sidedefs - укажем реальные текстуры
        sidedefs = [
            # offset_x, offset_y, upper, lower, middle, sector
            (0, 0, "STARGR2", "STARGR2", "STARGR2", 0),
        ]
        # Sectors - добавим exit sector
        sectors = [
            # floor, ceiling, floor_tex, ceil_tex, light, special, tag
            (0, wall_height, "SKY1", "FLAT5_1", 192, 0, 0),  # Main area 192
            (0, wall_height, "MFLR8_1", "MFLR8_1", 250, 0, 0),  # Main area 160
        ]
        
        # Things - добавим монстров и предметы
        things = [
            # Player start
            (width//2, height//2, 90, 1, 7),
            
            # Monsters
            (width//3, height//3, 0, 3004, 7),  # Imp
            (2*width//3, height//3, 0, 3004, 7),
            (width//2, height//4, 0, 3002, 7),  # Demon
            
            # Health
            (width//4, height//4, 0, 2014, 7),  # Medkit
            (3*width//4, height//4, 0, 2014, 7),
            
            # Ammo
            (width//4, 3*height//4, 0, 2007, 7),  # Clip
            (3*width//4, 3*height//4, 0, 2007, 7),
            (width//2, 3*height//4, 0, 2048, 7),  # Shells
            
            # Weapons
            (width//4, height//2, 0, 2005, 7),  # Shotgun
            
            # Exit switch (на северной стене)
            (width//2, height - 32, 0, 11, 7)
        ]
        
        # Blockmap
        blockmap = self.create_simple_blockmap(vertices, width, height)
        
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
            # Pack texture names to 8 bytes each
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
        lump_order = ['THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SECTORS']
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
    output_wad = "football-field.wad"
    
    print("Creating new WAD with MAP00...")
    processor = WADProcessor()
    processor.create_new_wad(output_wad)
    
    print("Done!")

if __name__ == "__main__":
    main()