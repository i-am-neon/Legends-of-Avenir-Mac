
import os
from os import walk
from os import path
import argparse

MUSIC_EVENTS = {'MUSC','MUSS'} # There are other codes, but I know I only use these...
PHASE_NAMES = {'Player Phase music','Enemy Phase music','NPC Phase music','Player Phase music 2','Enemy Phase music 2','NPC Phase music 2'}

parser = argparse.ArgumentParser()
parser.add_argument('event_path',help='Filepath to directory for scanning for events.')
parser.add_argument('chapter_data_table',help='Filepath to Chapter Data Table CSV.')
parser.add_argument('character_music_table',help='Filepath to Character Music Table CSV.')
parser.add_argument('other_refs',help='Filepath to other music reference declaration document.')
parser.add_argument('music_defs',help='Filepath to music definition S file.')
parser.add_argument('output',help='Filepath to output file.')
args = parser.parse_args()

MUSIC_REFS = []
NOT_REFERENCED = []
VANILLA_REFS = []

class SongRef:
    def __init__(self,song):
        self.song = song
        self.places = []

def getSongRef(song,refs):
    for i in refs:
        if i.song == song:
            return i
    return None

def addToRefList(song,place,refs):
    # If the passed in song is 0, don't add it.
    song = song.strip()
    place = place.strip()
    if song == '0': return
    # Does this song already exist in the list?
    ref = getSongRef(song,refs)
    if not ref:
        ref = SongRef(song)
        refs.append(ref)
    ref.places.append(place)

def getSong(ref):
    return ref.song

def getPhaseIndecies(phaseNames,header):
    ret = []
    for i,e in enumerate(header):
        if e in phaseNames: ret.append(i)
    return ret

def generateFinal(refs,notReffed,vanilla):
    yield 'Autogenerated music reference output:\nList of all music references:\n\n'
    for i in refs:
        yield i.song+'\n'
        for j in i.places: yield '\t'+j+'\n'
    yield '\n\nList of custom music never referenced:\n'
    for i in notReffed:
        yield i+'\n'
    yield '\n\nList of vanilla music being used:\n'
    for i in vanilla:
        yield i.song+'\n'
        for j in i.places: yield '\t'+j+'\n'

if __name__ == '__main__':
    for (dirpath, dirnames, filenames) in walk(os.getcwd()+'/'+args.event_path):
        for i,f in enumerate(filenames):
            if f.endswith('.event'):
                fullpath = dirpath[len(os.getcwd())+1:]+'\\'+f
                with open(fullpath,'r') as o:
                    for line in o:
                        for e in MUSIC_EVENTS:
                            if line.strip().startswith(e+' '):
                                song = line.strip().split()[1]
                                addToRefList(song,f,MUSIC_REFS)
    # MUSIC_REFS should be full of SongRef objects now.
    
    # Next, let's get phase themes and boss themes from CSVs.
    indecies = []
    with open(os.getcwd()+'/'+args.chapter_data_table) as o:
        for i,line in enumerate(o):
            if i == 0: indecies = getPhaseIndecies(PHASE_NAMES,line.split(','))
            else:
                entries = line.split(',')
                chapter = entries[0]
                for j in indecies:
                    if chapter != '' and not entries[j].startswith('0'): addToRefList(entries[j],'Phase theme: '+chapter,MUSIC_REFS)
        # MUSIC_REFS should have phase themes now.
    
    with open(os.getcwd()+'/'+args.character_music_table) as o:
        for i,line in enumerate(o):
            entries = line.split(',')
            character = entries[0]
            if i != 0 and character != '' and not entries[1].startswith('0'):
                addToRefList(entries[1],'Battle theme: '+entries[0],MUSIC_REFS)
        # MUSIC_REFS should have battle themes now.
    
    # Now we want to add references listed in the other ref document (for stuff like major game themes).
    for line in open(os.getcwd()+'/'+args.other_refs):
        # Format is just: "Song_Def,Place"
        entries = line.split(',')
        addToRefList(entries[0],entries[1],MUSIC_REFS)
    
    # Now let's alphabetize by the song name.
    MUSIC_REFS.sort(key=getSong)
    
    # Now I want to build a list of songs that are never referenced.
    # First let's fill that list with all songs in the music directory.
    with open(os.getcwd()+'/'+args.music_defs) as o:
        for line in o:
            if line.startswith('.'): continue
            entries = line.split()
            if entries[0].strip() != '': NOT_REFERENCED.append(entries[0].strip())
        for e in MUSIC_REFS:
            try:
                NOT_REFERENCED.remove(e.song) # We've successfully removed this song from the list.
            except ValueError:
                # This song is NOT in the list. Presumably, this is a vanilla song (or a typo). Add to the vanilla list.
                VANILLA_REFS.append(e)
    
    # Now all of our data is in place! Let's write to our output file.
    final = [e for e in generateFinal(MUSIC_REFS,NOT_REFERENCED,VANILLA_REFS)]
    with open(args.output,'w') as o:
        o.writelines(final)
