import re


fn = './Chopin_op10_no3.musicxml'
out_fn = './Chopin_op10_no3_rec.musicxml'
notes = []
note_info = False
with open(fn) as f:
    lines = f.read().splitlines()
    xml_lines = []
    for l in lines:
        if '<note id' in l:
            note_info = True
            note_attributes = []
        elif '</note>' in l:
            note_info = False
            note_attributes.append(l)
            notes.append(note_attributes)
            xml_lines.append(note_attributes)

        if note_info:
            note_attributes.append(l)
        elif '</note>' not in l:
            xml_lines.append(l)


def parse_notes(note):
    is_pitch = False
    is_notations = False

    chord = []
    grace = []
    pitch = []
    duration = []
    voice = []
    n_type = []
    dot = []
    stem = []
    staff = []
    notations = []
    tie = []
    head = []
    foot = []
    for l in note:
        if '<note' in l:
            head.append(l)
        if '</note' in l:
            foot.append(l)
        if '<pitch>' in l:
            is_pitch = True
        if '</pitch>' in l:
            is_pitch = False
            pitch.append(l)

        if '<notations>' in l:
            is_notations = True
        elif '</notations>' in l:
            is_notations = False
            notations.append(l)

        if is_pitch:
            pitch.append(l)
        if is_notations:
            notations.append(l)

        if '<duration>' in l:
            duration.append(l)
        if '<chord/>' in l:
            chord.append(l)
        if '<grace' in l:
            grace.append(l)
        if '<type>' in l:
            n_type.append(l)
        if '<dot/>' in l:
            dot.append(l)
        if '<tie type' in l:
            tie.append(l)
        if '<voice' in l:
            voice.append(l)
        if '<stem>' in l:
            stem.append(l)
        if '<staff>' in l:
            staff.append(l)

        # if '        <voice>4</voice>' in voice:
        #     print('change staff for voice 4')
        #     staff = ['        <staff>2</staff>']
        #     stem = ['        <stem>up</stem>']

    out_order = [
        head,
        grace,
        chord,
        pitch,
        # rest,
        # unpitched,
        duration,
        tie,
        voice,
        n_type,
        dot,
        stem,
        staff,
        notations,
        foot
    ]

    note_str = ''
    for p in out_order:
        if len(p) > 1:
            note_str += '\n'.join(p) + '\n'
        elif len(p) == 1:
            note_str += p[0] + '\n'

    return note_str[:-1]


out_xml = '\n'.join([parse_notes(l) if isinstance(l, list) else l for l in xml_lines])

with open(out_fn, 'w') as f:
    f.write(out_xml)
