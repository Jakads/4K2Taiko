from os.path import splitext
import sys
from msvcrt import getch
import traceback

class InvalidPatternException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

print('4K2Taiko v1.0.0')
print('by Jakads\n')

# need exactly one .osu file dragged in
if len(sys.argv) != 2:
    print('drag single file into this program.')
    getch()
    sys.exit()

print('1. ddkk')
print('2. kddk')
print('3. kkdd')
print('4. dkkd')

# repeat until 1~4 is pressed
while True:
    try:
        play_type = int(getch())
        if 1 <= play_type <= 4: break
    except:
        pass

# set IS_KAT for each column
if play_type == 1: IS_KAT = [False, False, True, True]
elif play_type == 2: IS_KAT = [True, False, False, True]
elif play_type == 3: IS_KAT = [True, True, False, False]
else: IS_KAT = [False, True, True, False]

# file_path = folder\file_name.osu
file_path = sys.argv[1]
# new_file_path = folder\file_name_taiko[play_type].osu
new_file_path = splitext(file_path)[0] + '_taiko' + str(play_type) + '.osu'

try:
    # open file and read all the lines (including \n)
    with open(file_path, encoding='utf-8') as osu:
        content = osu.readlines()
    
    # metadata_list = all the lines before [TimingPoints]
    # timing_list = timing points ([TimingPoints] ~ [HitObjects])
    # object_list = objects ([HitObjects] ~ EOF)

    timing_index = content.index('[TimingPoints]\n')
    object_index = content.index('[HitObjects]\n')
    metadata_list = content[:timing_index+1]
    timing_list = content[timing_index+1:object_index]
    object_list = content[object_index+1:]
    
    # save the new converted file content to new_osu_list
    new_osu_list = []

    for line in metadata_list:
        # change the game mode to taiko
        if line.startswith('Mode:'):
            new_line = 'Mode: 1\n'

        # add (taiko convert_[play_type]) to the difficulty name
        elif line.startswith('Version:'):
            original_version = line[8:-1]
            new_version = f'{original_version} (taiko convert_{play_type})'
            new_line = f'Version:{new_version}\n'

        # set BeatmapID to 0 so it's as if a diff is added to the mapset
        elif line.startswith('BeatmapID:'):
            new_line = 'BeatmapID:0\n'

        else:
            new_line = line
            
        new_osu_list.append(new_line)
    
    keys = 4
    # colrange = [0, 128, 256, 384, 512]
    colrange = [512*column/keys for column in range(keys+1)]
    
    # bpm_dict = {offset: bpm}
    bpm_dict = {}
    # note_dict = {offset: dk}
    note_dict = {}
    
    # save bpm to bpm_dict
    for timing in timing_list:
        timing_element = timing.split(',')
        
        # if it's a valid timing point:
        # time,beatLength,meter,sampleSet,sampleIndex,volume,uninherited,effects
        if len(timing_element) == 8:

            Uninherited = int(timing_element[6])
    
            if Uninherited:
                offset = float(timing_element[0])
                # beatLength = ms per beat
                # beats/min = (60s/min) * (1000s/ms) / (ms/beat)
                bpm = 60000 / float(timing_element[1])
                bpm_dict[offset] = bpm
        
        new_osu_list.append(timing)
    
    # save note to note_dict
    for note in object_list:
        note_element = note.split(',')

        # hit object = x,y,time,type,hitSound,objectParams,hitSample
        # type is written in binary
        # 1 = hitcircle, 2 = slider, 4 = newcombo, 8 = spinner,
        # 16~64 = related to combo colors, 128 = mania LN
        # for circles: no objectParams needed
        # for sliders: objectParams = curveType|curvePoints,slides,length,edgeSounds,edgeSets
        # for spinners & LNs: objectParams = endTime
    
        x = int(note_element[0])
        offset = int(note_element[2])

        # LN type = 128 or 128+4
        LN = True if note_element[3] == '128' or note_element[3] == '132' else False
        if LN:
            offset_end = int(note_element[5].split(':')[0])
    
        # if x is 0~128: it's col 1, and so on
        for i in range(keys):
            if colrange[i] <= x <= colrange[i+1]:
                column = i
        
        # add key if the offset key is not present in note_dict
        if offset not in note_dict:
            note_dict[offset] = []
        
        # if regular note: append [False, if the col is assigned as kat]
        if not LN:
            note_dict[offset].append([LN, IS_KAT[column]])
        # if LN: append [True, end ms of the LN]
        else:
            note_dict[offset].append([LN, offset_end])
    
    new_osu_list.append('\n[HitObjects]\n')
    
    # set default value to impossibly small one
    ln_end_offset = -1
    for offset, notes in note_dict.items():
        don_count, kat_count, ln_count = 0, 0, 0
    
        for note in notes:
            # whether it's LN or not
            LN = note[0]

            if not LN:
                # if the col is assigned as kat
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
        
        # if a note or LN overlap with a LN
        if offset <= ln_end_offset:
            raise InvalidPatternException(f'invalid pattern at {offset}ms')

        if LNCheck:
            for note in notes:
                # if LNs at current ms doesn't end at same ms
                if note[1] != offset_end:
                    raise InvalidPatternException(f'invalid pattern at {offset_end}ms')
        
        # if Slider is created
        if Slider:
            # find current bpm
            for bpm_offset in bpm_dict.keys():
                if offset >= bpm_offset:
                    bpm_offset_now = bpm_offset
                else:
                    break
            bpm = bpm_dict[bpm_offset]
            length = offset_end - offset
            # round the beat to 1/16, 1/12 snaps
            beat = round(length / (60000 / bpm) * 48) / 48
            # calculated out of trial and error
            slider_length = beat * 130
            # linear slider from (256,192) to (257,192)
            extra += 'L|257:192,1,' + str(slider_length)
            ln_end_offset = offset_end
        
        new_osu_list.append(f'256,192,{offset},{extra}\n')
    
    # write new osu file according to new_osu_list
    with open(new_file_path,mode='w',encoding='utf-8') as osu:
        for line in new_osu_list:
            osu.write(line)

    print('done.')
    getch()
    sys.exit()

except:
    # if any exceptions occur, print the traceback
    print(traceback.format_exc())
    getch()
    sys.exit()