import struct
import sys
import os
import glob

def extract_first_frame(ani_path, out_dir):
    with open(ani_path, 'rb') as f:
        data = f.read()

    if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'ACON':
        print(f"Skipping {ani_path}: Not a valid ANI file")
        return

    offset = 12
    while offset < len(data):
        chunk_id = data[offset:offset+4]
        chunk_size = struct.unpack('<I', data[offset+4:offset+8])[0]
        chunk_data = data[offset+8:offset+8+chunk_size]
        
        if chunk_id == b'LIST':
            list_type = chunk_data[:4]
            if list_type == b'fram':
                # Parse frames
                frame_offset = 4
                while frame_offset < len(chunk_data):
                    sub_id = chunk_data[frame_offset:frame_offset+4]
                    sub_size = struct.unpack('<I', chunk_data[frame_offset+4:frame_offset+8])[0]
                    sub_data = chunk_data[frame_offset+8:frame_offset+8+sub_size]
                    
                    if sub_id == b'icon':
                        # Found the first icon/cur data!
                        base_name = os.path.basename(ani_path).replace('.ani', '')
                        out_path = os.path.join(out_dir, f"{base_name}.cur")
                        with open(out_path, 'wb') as out_f:
                            out_f.write(sub_data)
                        print(f"Extracted {out_path}")
                        return
                    
                    frame_offset += 8 + sub_size + (sub_size % 2)
        
        offset += 8 + chunk_size + (chunk_size % 2)

if __name__ == '__main__':
    src_dir = r"c:\Users\Eagle\Documents\Personal Files\Projects\Custom-Cursors-Linux\Cursor Demos\Aemeath- BLZ Free\Trial"
    dest_dir = r"c:\Users\Eagle\Documents\Personal Files\Projects\Custom-Cursors-Linux\demo-cursors\Aemeath"
    os.makedirs(dest_dir, exist_ok=True)
    
    for ani_file in glob.glob(os.path.join(src_dir, '*.ani')):
        extract_first_frame(ani_file, dest_dir)
