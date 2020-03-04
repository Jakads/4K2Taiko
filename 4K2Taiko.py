from os.path import splitext
import sys
from msvcrt import getch
import traceback

class InvalidPatternException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

print('4K2Taiko v1.0.0')
print('by Jakads\n')

if len(sys.argv) != 2:
    print('drag single file into this program.')
    getch()
    exit()

file_path = sys.argv[1]

print('1. ddkk')
print('2. kddk')
print('3. kkdd')
print('4. dkkd')
while True:
    try:
        play_type = int(getch())
        if 1 <= play_type <= 4: break
    except:
        pass

if play_type == 1: IS_KAT = [False, False, True, True]
elif play_type == 2: IS_KAT = [True, False, False, True]
elif play_type == 3: IS_KAT = [True, True, False, False]
else: IS_KAT = [False, True, True, False]

new_file_path = splitext(file_path)[0] + '_taiko' + str(play_type) + '.osu'

try:
    with open(file_path, encoding='utf-8') as osu:
        content = osu.readlines()
    
    timing_index = content.index('[TimingPoints]\n')
    object_index = content.index('[HitObjects]\n')
    metadata_list = content[:timing_index+1]
    timing_list = content[timing_index+1:object_index]
    object_list = content[object_index+1:]
    
    new_osu_list = []
    for line in metadata_list:
        if line.startswith('Mode:'):
            new_line = 'Mode: 1\n'
        elif line.startswith('Version:'):
            original_version = line[8:-1]
            new_version = f'{original_version} (taiko convert_{play_type})'
            new_line = f'Version:{new_version}\n'
        elif line.startswith('BeatmapID:'):
            new_line = 'BeatmapID:0\n'
        else:
            new_line = line
        new_osu_list.append(new_line)
    
    keys = 4
    colrange = [512*column/keys for column in range(keys+1)]
    
    # bpm_dict = {offset: bpm}
    bpm_dict = {}
    # note_dict = {offset: dk}
    note_dict = {}
    
    for timing in timing_list:
        timing_element = timing.split(',')
        if len(timing_element) != 8: continue
    
        Uninherited = int(timing_element[6])
        offset = float(timing_element[0])
        bpm = 60000 / float(timing_element[1])
    
        if Uninherited:
            bpm_dict[offset] = bpm
        
        new_osu_list.append(timing)
    
    for note in object_list:
        note_element = note.split(',')
    
        x = int(note_element[0])
        offset = int(note_element[2])
        LN = True if note_element[3] == '128' or note_element[3] == '132' else False
        if LN:
            offset_end = int(note_element[5].split(':')[0])
    
        for i in range(keys):
            if colrange[i] <= x <= colrange[i+1]:
                column = i
        
        if offset not in note_dict:
            note_dict[offset] = []
        if not LN:
            note_dict[offset].append([LN, IS_KAT[column]])
        else:
            note_dict[offset].append([LN, offset_end])
    
    new_osu_list.append('\n[HitObjects]\n')
    
    ln_end_offset = -1
    for offset, notes in note_dict.items():
        don_count, kat_count, ln_count = 0, 0, 0
    
        for note in notes:
            LN = note[0]
            if not LN:
                if note[1]:
                    kat_count += 1
                else:
                    don_count += 1
            else:
                ln_count += 1
                offset_end = note[1]
        
        count = ln_count * 100 + kat_count * 10 + don_count
        Slider = False
        LNCheck = False
        if count == 1:      # don
            extra = '1,0'
        elif count == 2:    # DON
            extra = '1,4'
        elif count == 10:   # kat
            extra = '1,8'
        elif count == 20:   # KAT
            extra = '1,12'
        elif count == 100:  # slider
            extra = '2,0,'
            Slider = True
        elif count == 200:  # SLIDER
            extra = '2,4,'
            Slider = True
            LNCheck = True
        elif count == 400:  # spinner
            extra = '8,0,' + str(offset_end)
            LNCheck = True
        else:               # invalid
            raise InvalidPatternException(f'invalid pattern at {offset}ms')
        
        if offset <= ln_end_offset:
            raise InvalidPatternException(f'invalid pattern at {offset}ms')

        if LNCheck:
            for note in notes:
                if note[1] != offset_end:
                    raise InvalidPatternException(f'invalid pattern at {offset_end}ms')

        if Slider:
            for bpm_offset in bpm_dict.keys():
                if offset >= bpm_offset:
                    bpm_offset_now = bpm_offset
                else:
                    break
            bpm = bpm_dict[bpm_offset]
            length = offset_end - offset
            beat = round(length / (60000 / bpm) * 48) / 48
            slider_length = beat * 130
            extra += 'L|257:192,1,' + str(slider_length)
            ln_end_offset = offset_end
        
        new_osu_list.append(f'256,192,{offset},{extra}\n')
    
    with open(new_file_path,mode='w',encoding='utf-8') as osu:
        for line in new_osu_list:
            osu.write(line)

    print('done.')
    getch()

except:
    print(traceback.format_exc())
    getch()