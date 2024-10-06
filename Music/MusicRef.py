import os
import argparse

MUSIC_EVENTS = {'MUSC', 'MUSS'}  # There are other codes, but I know I only use these...
PHASE_NAMES = {'Player Phase music', 'Enemy Phase music', 'NPC Phase music',
               'Player Phase music 2', 'Enemy Phase music 2', 'NPC Phase music 2'}
ATTACK_NAME = {'Attack Theme'}
DEFENSE_NAME = {'Defense Theme'}

parser = argparse.ArgumentParser()
parser.add_argument('event_path', help='Filepath to directory for scanning for events.')
parser.add_argument('chapter_data_table', help='Filepath to Chapter Data Table CSV.')
parser.add_argument('character_music', help='Filepath to PersonalMusic.event.')  # Used to be the character music table, but I changed this to an event installer.
parser.add_argument('other_refs', help='Filepath to other music reference declaration document.')
parser.add_argument('music_defs', help='Filepath to music definition S file.')
parser.add_argument('output', help='Filepath to output file.')
args = parser.parse_args()

MUSIC_REFS = []
NOT_REFERENCED = []
VANILLA_REFS = []

class SongRef:
    def __init__(self, song):
        self.song = song
        self.places = []

def getSongRef(song, refs):
    for i in refs:
        if i.song == song:
            return i
    return None

def addToRefList(song, place, refs):
    # If the passed in song is 0, don't add it.
    song = song.strip()
    place = place.strip()
    if song == '' or song.startswith('0'):
        return
    # Does this song already exist in the list?
    ref = getSongRef(song, refs)
    if not ref:
        # This song hasn't been referenced yet.
        ref = SongRef(song)
        refs.append(ref)
    else:
        # This song has been referenced. Let's check to see if this location is already recorded.
        if place in ref.places:
            return
    ref.places.append(place)

def getSong(ref):
    return ref.song

def getIndexes(columnNames, header):
    ret = []
    for i, e in enumerate(header):
        if e.strip() in columnNames:
            ret.append(i)
    return ret

def generateFinal(refs, notReffed, vanilla):
    yield '#AUTOGENERATED MUSIC REFERENCE OUTPUT#\n\nList of all music references:\n\n'
    for i in refs:
        yield i.song + '\n'
        for j in i.places:
            yield '\t' + j + '\n'
    yield '\n\nList of custom music never referenced:\n'
    for i in notReffed:
        yield i + '\n'
    yield '\n\nList of vanilla music being used:\n'
    for i in vanilla:
        yield i.song + '\n'
        for j in i.places:
            yield '\t' + j + '\n'

if __name__ == '__main__':
    event_path = os.path.abspath(args.event_path)
    for dirpath, dirnames, filenames in os.walk(event_path):
        for f in filenames:
            if f.endswith('.event'):
                fullpath = os.path.join(dirpath, f)
                with open(fullpath, 'r') as o:
                    for line in o:
                        for e in MUSIC_EVENTS:
                            if line.strip().startswith(e + ' '):
                                song = line.strip().split()[1]
                                addToRefList(song, f, MUSIC_REFS)
    # MUSIC_REFS should be full of SongRef objects now.

    # Next, let's get phase themes and boss themes from CSVs.
    phaseIndexes = []
    chapter_data_table_path = os.path.abspath(args.chapter_data_table)
    with open(chapter_data_table_path, 'r') as o:
        for i, line in enumerate(o):
            splitted = line.strip().split(',')
            if i == 0:
                phaseIndexes = getIndexes(PHASE_NAMES, splitted)
                attackIndex = getIndexes(ATTACK_NAME, splitted)[0]
                defenseIndex = getIndexes(DEFENSE_NAME, splitted)[0]
            else:
                chapter = splitted[0]
                for k, j in enumerate(phaseIndexes):
                    if chapter != '' and not splitted[j].startswith('0'):
                        themes = ['Player phase theme: ', 'Enemy phase theme: ', 'NPC phase theme: ',
                                  'Player phase theme: ', 'Enemy phase theme: ', 'NPC phase theme: ']
                        addToRefList(splitted[j], themes[k] + chapter, MUSIC_REFS)
                if chapter != '' and not splitted[attackIndex].startswith('0'):
                    addToRefList(splitted[attackIndex], 'Attack theme: ' + chapter, MUSIC_REFS)
                if chapter != '' and not splitted[defenseIndex].startswith('0'):
                    addToRefList(splitted[defenseIndex], 'Defense theme: ' + chapter, MUSIC_REFS)
        # MUSIC_REFS should have phase themes now.

    character_music_path = os.path.abspath(args.character_music)
    with open(character_music_path, 'r') as o:
        for line in o:
            line = line.split('//')[0]
            if not line.startswith('CharacterMusic('):
                continue
            entries = line.strip().split(',')
            character = entries[0][len('CharacterMusic('):]
            chapter = entries[1]
            song = entries[2].rstrip(');').strip()
            addToRefList(song, f'Battle theme at {chapter} for {character}', MUSIC_REFS)
        # MUSIC_REFS should have character battle themes now.

    # Now we want to add references listed in the other ref document (for stuff like major game themes).
    other_refs_path = os.path.abspath(args.other_refs)
    with open(other_refs_path, 'r') as o:
        for line in o:
            # Format is just: "Song_Def,Place"
            entries = line.strip().split(',')
            if len(entries) >= 2:
                addToRefList(entries[0], entries[1], MUSIC_REFS)

    # Now let's alphabetize by the song name.
    MUSIC_REFS.sort(key=getSong)

    # Now I want to build a list of songs that are never referenced.
    # First let's fill that list with all songs in the music directory.
    music_defs_path = os.path.abspath(args.music_defs)
    with open(music_defs_path, 'r') as o:
        for line in o:
            if line.startswith('.'):
                continue
            entries = line.strip().split()
            if entries and entries[0].strip() != '':
                NOT_REFERENCED.append(entries[0].strip())
        for e in MUSIC_REFS:
            try:
                NOT_REFERENCED.remove(e.song)  # We've successfully removed this song from the list.
            except ValueError:
                # This song is NOT in the list. Presumably, this is a vanilla song (or a typo). Add to the vanilla list.
                VANILLA_REFS.append(e)

    # Now all of our data is in place! Let's write to our output file.
    final = list(generateFinal(MUSIC_REFS, NOT_REFERENCED, VANILLA_REFS))
    output_path = os.path.abspath(args.output)
    with open(output_path, 'w') as o:
        o.writelines(final)