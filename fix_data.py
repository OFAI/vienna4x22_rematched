#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script fixes some data problems described in changes.txt
"""

import os
import glob
import numpy as np
import pandas as pd

import partitura as pt
import parangonar as pa

import warnings
warnings.filterwarnings('ignore')

# existing data
score_dir = os.path.join(os.getcwd(), 'musicxml')
midi_dir = os.path.join(os.getcwd(), 'midi')
match_dir = os.path.join(os.getcwd(), 'match')
# updated data
upd_match_dir = os.path.join(os.getcwd(), 'updated_match')
# for parangonar testing
match_align_dir = os.path.join(os.getcwd(), 'match_alignments') 
match_parangonar_align_dir = os.path.join(os.getcwd(), 'match_alignments_parangonar') 
upd_match_align_dir = os.path.join(os.getcwd(), 'updated_match_alignments') 
upd_parangonar_match_align_dir = os.path.join(os.getcwd(), 'updated_match_alignments_parangonar') 

for dir in [upd_match_dir, match_align_dir, match_parangonar_align_dir, upd_match_align_dir, upd_parangonar_match_align_dir]:
    if not os.path.exists(dir):
        os.mkdir(dir)

PIECES = [
    "Chopin_op38", 
    "Chopin_op10_no3", 
    "Mozart_K331_1st-mov", 
    "Schubert_D783_no15"
    ]


def test_parangonar_wrapper(aligner, sna, pna, gt_alignment=None, compare=False, fp=None):
    if compare == True:
        pred_alignment = aligner(sna, pna)
        # compute f-score and print the results
        with open(fp, 'w') as f:
            print('------------------', file=f)
            types = ['match','insertion', 'deletion']
            f_scores = np.zeros(3)
            for i, alignment_type in enumerate(types):
                precision, recall, f_score = pa.fscore_alignments(pred_alignment, 
                                                                gt_alignment, 
                                                                alignment_type)
                print('Evaluate ',alignment_type, file=f)
                print('Precision: ',format(precision, '.3f'),
                    'Recall ',format(recall, '.3f'),
                    'F-Score ',format(f_score, '.3f'), file=f)
                print('------------------', file=f)
                f_scores[i] = f_score
        return pred_alignment, f_scores
    
    else:
        pred_alignment = aligner(sna, pna)
        return pred_alignment
    



# for piece in PIECES[:1]:
for piece in PIECES:
    
    # Get unique score onsets and max beat
    score = pt.load_score(os.path.join(score_dir, f"{piece}.musicxml"))
    # score = pt.load_score(os.path.join(score_dir, f"{piece}_test.musicxml")) # changed file
    score_part = score.parts[0]
    sna = score_part.note_array()
    sna_ids = sna['id']
    unique_snotes_onset_idxs, unique_snotes_onsets_beat = pt.musicanalysis.performance_codec.get_unique_onset_idxs(sna["onset_beat"], return_unique_onsets=True)
    print(f'Piece: {piece} | score has {len(unique_snotes_onset_idxs)} unique onsets and max beat onset {max(unique_snotes_onsets_beat)}')
    
    # Get all midi files
    midi_files = glob.glob(os.path.join(midi_dir, f"{piece}_p*.mid"))
    midi_files.sort()
    
    # Get all match files
    # match_files = glob.glob(os.path.join(upd_match_dir, f"{piece}_p*.match"))
    match_files = glob.glob(os.path.join(match_dir, f"{piece}_p*.match"))
    match_files.sort()
    
    # num_files = 1
    # midi_files = midi_files[:num_files]
    # match_files = match_files[:num_files]
    
    match_parangonar_f_scores = np.zeros((22,3)) # 22 performances
    
    for perf_i, (midi_file, match_file) in enumerate(zip(midi_files, match_files)):
        print(f'Perf no.{perf_i+1:2d}', midi_file[-7:], match_file[-9:])
        
        midi_perf = pt.load_performance_midi(midi_file, merge_tracks=True)
        midi_ppart = midi_perf.performedparts[0]
        midi_pna = midi_ppart.note_array()
        midi_pna_ids = midi_pna['id']
        
        # Get score, alignment, perf from match
        # README match line decoding
        # score part:
        # snote(Anchor,[NoteName,Modifier],Octave,Measure:Beat,Offset,Duration,OnsetInBeats,OffsetInBeats,ScoreAttributesList).
        # perf part:
        # note(ID,MIDIpitch,OnsetTick,OffsetTick,Velocity).
        match_perf, match_align, match_score = pt.load_match(match_file, create_score=True)
        match_pna = match_perf.performedparts[0].note_array()
        match_pna_ids = match_pna['id']
        match_sna = match_score.parts[0].note_array()
        match_sna_ids = match_sna['id']
        pd.DataFrame(match_align).to_csv(os.path.join(match_align_dir, f'{piece}_p{perf_i+1:02d}.csv'), index=None)
        # # Test parangonar for old alignments:
        # sdm = pa.AutomaticNoteMatcher()
        # pa_test = os.path.join(match_parangonar_align_dir, f'{piece}_p{perf_i+1:02d}.txt')
        # pred_alignment, f_scores = test_parangonar_wrapper(sdm, match_sna, match_pna, gt_alignment=match_align, compare=True, fp=pa_test)
        # match_parangonar_f_scores[perf_i] = f_scores
        # pa_align_csv = os.path.join(match_parangonar_align_dir, f'{piece}_p{perf_i+1:02d}.csv')
        # pd.DataFrame(pred_alignment).to_csv(pa_align_csv, index=None)
        
        # Check MIDI and MATCH PERFORMANCE equality
        # Count deletions 
        del_count = sum(1 for d in match_align if d.get('label') == 'deletion')
        del_ids = [d.get('score_id') for d in match_align if d.get('label') == 'deletion']
        # print(f'{del_count} Match deletions: {del_ids}')
        if midi_pna.shape[0] != match_pna.shape[0]:
            missing_midi_notes = list(set(midi_pna_ids) - set(match_pna_ids))
            # if missing_midi_notes:
            #     print(f'{len(missing_midi_notes)} Midi notes missing in match:', missing_midi_notes)
            #     for mmn in missing_midi_notes:
            #         idxs = np.where([midi_pna['id'] == mmn])
                    # for idx in idxs[1:]:
                    #     print(midi_pna[idx[0]])
            missing_match_notes = list(set(match_pna_ids) - set(midi_pna_ids))
            if missing_match_notes:
                print(f'Match notes missing in midi:', missing_match_notes)
        # Check XML SCORE and MATCH SCORE equality
        if sna.shape[0] != match_sna.shape[0]:
            missing_xml_notes = list(set(sna_ids) - set(match_sna_ids))
            missing_xml_notes = [note for note in missing_xml_notes if 'voice_overlap' not in note]
            if missing_xml_notes:
                # print(f'XML notes missing in match:', missing_xml_notes)
                for mxn in missing_xml_notes:
                    idxs = np.where([sna['id'] == mxn])
                    # for idx in idxs[1:]:
                    #     print(sna[idx[0]])
            missing_match_snotes = list(set(match_sna_ids) - set(sna_ids))
            if missing_match_snotes:
                print(f'Match score notes missing in XML:', missing_match_snotes)
    
        # path for new matchfiles
        fp = os.path.join(upd_match_dir, f'{piece}_p{perf_i+1:02d}.match')
        
        # Piecewise fixes
        if piece == 'Chopin_op38':
            last_midi_note = midi_pna[-1]
            last_midi_note_id = last_midi_note['id']
            # check if the last performed note is missing in match files
            if last_midi_note_id in missing_midi_notes:
                last_alignment_dict = match_align[-1]
                if last_alignment_dict['label'] == 'deletion':
                    # print('Deleting: ', last_alignment_dict)
                    # cut the last alignment
                    match_align = match_align[:-1]
                    last_note_alignment = {'label': 'match', 'score_id': last_alignment_dict['score_id'], 'performance_id': last_midi_note['id']}
                    # print('Inserting: ', last_note_alignment)
                    match_align.append(last_note_alignment)            
            if not os.path.isfile(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')):
                # pt.save_match(match_align, midi_ppart, score_part, out=fp, performer = f'Pianist {perf_i+1:02d}', composer='Frèdéryk Chopin', piece=piece, score_filename=f'{piece}.musicxml', performance_filename = f'{piece}_p{perf_i+1:02d}.mid', assume_unfolded=True)
                pd.DataFrame(match_align).to_csv(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv'), index=None)
            # # parangonar test
            # pa_update_csv = os.path.join(upd_parangonar_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')
            # pred_alignment = test_parangonar_wrapper(sdm, sna, midi_pna)    
            # pd.DataFrame(pred_alignment).to_csv(pa_update_csv, index=None)
        
        elif piece == 'Chopin_op10_no3':
            # TODO fix for B3.
            if not os.path.isfile(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')):
                # pt.save_match(match_align, midi_ppart, score_part, out=fp, performer = f'Pianist {perf_i+1:02d}', composer='Frèdéryk Chopin', piece=piece, score_filename=f'{piece}.musicxml', performance_filename = f'{piece}_p{perf_i+1:02d}.mid', assume_unfolded=True)
                pd.DataFrame(match_align).to_csv(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv'), index=None)
            # # parangonar test
            # pa_update_csv = os.path.join(upd_parangonar_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')
            # pred_alignment = test_parangonar_wrapper(sdm, sna, midi_pna)    
            # pd.DataFrame(pred_alignment).to_csv(pa_update_csv, index=None)
        
        
        elif piece == 'Mozart_K331_1st-mov':
            if not os.path.isfile(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')):
                # pt.save_match(match_align, midi_ppart, score_part, out=fp, performer = f'Pianist {perf_i+1:02d}', composer='W. A. Mozart', piece=piece, score_filename=f'{piece}.musicxml', performance_filename = f'{piece}_p{perf_i+1:02d}.mid', assume_unfolded=True)
                pd.DataFrame(match_align).to_csv(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv'), index=None)
            # # parangonar test
            # pa_update_csv = os.path.join(upd_parangonar_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')
            # pred_alignment = test_parangonar_wrapper(sdm, sna, midi_pna)    
            # pd.DataFrame(pred_alignment).to_csv(pa_update_csv, index=None)
        
        
        elif piece == 'Schubert_D783_no15':
            if not os.path.isfile(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')):
                # pt.save_match(match_align, midi_ppart, score_part, out=fp, performer = f'Pianist {perf_i+1:02d}', composer='Franz Schubert', piece=piece, score_filename=f'{piece}.musicxml', performance_filename = f'{piece}_p{perf_i+1:02d}.mid', assume_unfolded=True)
                pd.DataFrame(match_align).to_csv(os.path.join(upd_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv'), index=None)
            # # parangonar test
            # pa_update_csv = os.path.join(upd_parangonar_match_align_dir, f'{piece}_p{perf_i+1:02d}.csv')
            # pred_alignment = test_parangonar_wrapper(sdm, sna, midi_pna)    
            # pd.DataFrame(pred_alignment).to_csv(pa_update_csv, index=None)
        print()
        
    match_avg_f_score = np.mean(match_parangonar_f_scores[:,0])
    ins_avg_f_score = np.mean(match_parangonar_f_scores[:,1])
    del_avg_f_score = np.mean(match_parangonar_f_scores[:,2])
    print(f'Average parangonar alignment f_scores: \n---match: {match_avg_f_score:.4f}\n---insertions: {ins_avg_f_score:.4f}\n---deletions: {del_avg_f_score:.4f}')
    
    print(42*'=')