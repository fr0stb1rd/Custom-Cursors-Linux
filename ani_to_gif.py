import struct
import sys
import os
import glob
import io
from PIL import Image

def parse_cur_frame(cur_data):
    try:
        num_images = struct.unpack('<H', cur_data[4:6])[0]
        width = cur_data[6]
        height = cur_data[7]
        if width == 0: width = 256
        if height == 0: height = 256
        
        image_offset = struct.unpack('<I', cur_data[18:22])[0]
        header_size = struct.unpack('<I', cur_data[image_offset:image_offset+4])[0]
        
        if header_size == 40:
            img_width, img_height, planes, bit_count = struct.unpack('<iiHH', cur_data[image_offset+4:image_offset+16])
            
            if bit_count == 32:
                real_height = img_height // 2 if img_height > 0 else abs(img_height)
                pixel_offset = image_offset + 40
                expected_size = width * real_height * 4
                
                if pixel_offset + expected_size <= len(cur_data):
                    pixels = cur_data[pixel_offset:pixel_offset + expected_size]
                    img = Image.frombytes("RGBA", (width, real_height), pixels, "raw", "BGRA")
                    if img_height > 0:
                        img = img.transpose(Image.FLIP_TOP_BOTTOM)
                        
                    # CRITICAL FIX: Un-premultiply the alpha to fix the black border and washed out colors!
                    # Windows cursors often store colors pre-multiplied by alpha.
                    data = list(img.getdata())
                    new_data = []
                    for r, g, b, a in data:
                        if 0 < a < 255:
                            # Un-multiply to restore original vibrant color
                            r = min(255, int((r * 255) / a))
                            g = min(255, int((g * 255) / a))
                            b = min(255, int((b * 255) / a))
                        new_data.append((r, g, b, a))
                    img.putdata(new_data)
                    
                    return img
    except Exception as e:
        pass
        
    return Image.open(io.BytesIO(cur_data)).convert("RGBA")

def convert_ani_to_apng(ani_path, out_dir):
    with open(ani_path, 'rb') as f:
        data = f.read()

    if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'ACON':
        return

    frames = []
    jif_rate = 8
    rates = []
    seq = []
    
    offset = 12
    while offset < len(data):
        chunk_id = data[offset:offset+4]
        if len(data) < offset+8:
            break
        chunk_size = struct.unpack('<I', data[offset+4:offset+8])[0]
        chunk_data = data[offset+8:offset+8+chunk_size]
        
        if chunk_id == b'anih':
            anih = struct.unpack('<IIIIIIIII', chunk_data[:36])
            jif_rate = anih[7]
        elif chunk_id == b'rate':
            rates = struct.unpack(f'<{len(chunk_data)//4}I', chunk_data)
        elif chunk_id == b'seq ':
            seq = struct.unpack(f'<{len(chunk_data)//4}I', chunk_data)
        elif chunk_id == b'LIST':
            list_type = chunk_data[:4]
            if list_type == b'fram':
                frame_offset = 4
                while frame_offset < len(chunk_data):
                    sub_id = chunk_data[frame_offset:frame_offset+4]
                    if len(chunk_data) < frame_offset+8:
                        break
                    sub_size = struct.unpack('<I', chunk_data[frame_offset+4:frame_offset+8])[0]
                    sub_data = chunk_data[frame_offset+8:frame_offset+8+sub_size]
                    
                    if sub_id == b'icon':
                        frames.append(sub_data)
                    
                    frame_offset += 8 + sub_size + (sub_size % 2)
        
        offset += 8 + chunk_size + (chunk_size % 2)
        
    if not frames:
        return
    if not seq:
        seq = list(range(len(frames)))
    if not rates:
        rates = [jif_rate] * len(seq)
    if len(rates) < len(seq):
        rates = list(rates) + [jif_rate] * (len(seq) - len(rates))

    pil_frames = []
    durations = []
    for step, rate in zip(seq, rates):
        if step >= len(frames):
            continue
        try:
            img = parse_cur_frame(frames[step])
            pil_frames.append(img)
            durations.append(int((rate / 60.0) * 1000))
        except Exception as e:
            pass
            
    if pil_frames:
        base_name = os.path.basename(ani_path).replace('.ani', '')
        out_path = os.path.join(out_dir, f"{base_name}.png")
        
        if len(pil_frames) == 1:
            pil_frames[0].save(out_path, format="PNG")
        else:
            pil_frames[0].save(
                out_path, 
                format="PNG",
                save_all=True, 
                append_images=pil_frames[1:], 
                duration=durations, 
                loop=0, 
                disposal=2 # Essential for proper APNG transparency frame clearing
            )
        print(f"Successfully converted {ani_path} to {out_path} with PERFECT transparency!")

if __name__ == '__main__':
    src_dir = r"c:\Users\Eagle\Documents\Personal Files\Projects\Custom-Cursors-Linux\Cursor Demos\Aemeath- BLZ Free\Trial"
    dest_dir = r"c:\Users\Eagle\Documents\Personal Files\Projects\Custom-Cursors-Linux\demo-cursors\Aemeath"
    os.makedirs(dest_dir, exist_ok=True)
    
    for ani_file in glob.glob(os.path.join(src_dir, '*.ani')):
        convert_ani_to_apng(ani_file, dest_dir)
