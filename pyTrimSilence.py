#!/usr/bin/env python
# coding=utf-8
#
import argparse
import os
import sys
import datetime
from pydub import AudioSegment
from send2trash import send2trash


def convert_ms_to_timestring(ms):
    millisecs = 0
    secs = 0
    mins = 0
    secs, millisecs = divmod(ms, 1000)
    mins, secs = divmod(secs, 60)

    return '{:02d}:{:02d}.{:03d}'.format(mins, secs, millisecs)



def my_print(verbose, msg):
    if verbose:
        print msg



# def detect_leading_silence(sound, silence_threshold, chunk_size=1):
#     counter_ms = 0 # ms
#     while sound[counter_ms:counter_ms+chunk_size].dBFS < silence_threshold:
#         level = sound[counter_ms:counter_ms+chunk_size].dBFS
#         #print "Level: {} dB at {}".format(level, convert_ms_to_timestring(counter_ms))
#         trim_ms = counter_ms
#         counter_ms += chunk_size
#
#     #print "Returning {} ms".format(convert_ms_to_timestring(trim_ms))
#     return trim_ms



def detect_leading_silence(sound, silence_threshold, chunk_size=1):
    counter_ms = 0 # ms
    sound_length = len(sound) - 1
    while True:
        level = sound[counter_ms:counter_ms+chunk_size].dBFS
        print "Level: {} dB at {}".format(level, convert_ms_to_timestring(counter_ms))
        if level > silence_threshold or counter_ms == sound_length:
            break
        counter_ms += chunk_size

    if counter_ms == sound_length:
        counter_ms = 0
    print "Returning {} ms".format(convert_ms_to_timestring(counter_ms))
    return counter_ms



def main():

    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Command line tool for trimming silence from beginning and end of an '
                                                 'AIFF audio file.')
    parser.add_argument('filename',
                        help='audio file to trim')
    parser.add_argument('-t',
                        dest='threshold',
                        metavar='dB',
                        default=-96.0,
                        help='threshold (default: -96.0 dB)')
    parser.add_argument('-b',
                        dest='b_offset',
                        metavar='ms',
                        default=0,
                        help='beginning offset (default: 0 ms)')
    parser.add_argument('-e',
                        dest='e_offset',
                        metavar='ms',
                        default=0,
                        help='ending offset (default: 0 ms)')
    parser.add_argument('--test',
                        action='store_true',
                        help='perform test run without making changes')
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='increase output verbosity')
    args = parser.parse_args()


    
    # Initialize required variables
    starttime = datetime.datetime.now()
    filename = args.filename
    threshold = args.threshold
    b_offset = args.b_offset
    e_offset = args.e_offset
    test = args.test
    v = args.verbose
    filename = os.path.expanduser(filename)
    filename = os.path.expandvars(filename)
    file_location, file_tail = os.path.split(filename)
    file_basename = os.path.splitext(file_tail)[0]
    file_ext = os.path.splitext(file_tail)[1]
    file_ext = file_ext[1:] #Strip leading dot
    file_ext = file_ext.lower()
    supported_extensions = ('aiff', 'aif')

    
    
    # Input validation
    if file_ext in supported_extensions:
        pydubformat = file_ext.lower()[:3]
    else:
        #unsupported file format
        print '\'{}\' is not a file type supported by this script!'.format(file_ext.upper())
        sys.exit(-1)
    # Obtain audio segment from file
    try:
        sound = AudioSegment.from_file(filename)
    except IOError as e:
        print "I/O error({0}): {1}: '{2}'".format(e.errno, e.strerror, filename)
        sys.exit(-1)



    # Initialize additional variables
    file_type = file_ext
    if file_type == 'aif':
        file_type = 'aiff'
    file_type = file_type.upper()
    duration_ms = len(sound)

    
    
    # Display info
    # my_print(v, 'Start time                 :  {}'.format(starttime))
    my_print(v, 'File to trim               :  {}'.format(filename))
    # my_print(v, 'File location              :  {}'.format(file_location))
    # my_print(v, 'File basename              :  {}'.format(file_basename))
    # my_print(v, 'File extension             :  {}'.format(file_ext))
    my_print(v, 'File type                  :  {}'.format(file_type))
    my_print(v, 'Threshold (db)             :  {}'.format(threshold))
    my_print(v, 'Beginning Offset (ms)      :  {:+}'.format(b_offset))
    my_print(v, 'Ending Offset (ms)         :  {:+}'.format(e_offset))
    # my_print(v, 'Duration (ms)              :  {}'.format(duration_ms))
    my_print(v, 'Duration (m:s.ms)          :  {}'.format(convert_ms_to_timestring(duration_ms)))



    # Detect silence from beginning and end of audio segment
    start_trim = detect_leading_silence(sound, threshold, chunk_size=1)
    end_trim = detect_leading_silence(sound.reverse(), threshold, chunk_size=1)
    my_print(v, 'Start trim                 :  {}'.format(convert_ms_to_timestring(start_trim)))
    my_print(v, 'End trim                   :  {}'.format(convert_ms_to_timestring(end_trim)))

    # Adjust for user-specified offset from beginning of audio segment
    if start_trim > 0:  # Proceed if silence detected at beginning of audio segment
        if b_offset < 0:  # If negative offset specified
            if start_trim >= abs(b_offset):  # Apply offset if silence is long enough
                start_trim -= abs(b_offset)
        if b_offset > 0:  # If positive offset specified
            if b_offset < (duration_ms - (start_trim + end_trim)):  # Apply offset if audio segment is long enough
                if end_trim > 0:  # Proceed if silence detected at end of audio segment
                    if e_offset < 0:  # If negative offset specified
                        if b_offset < (duration_ms - (start_trim + end_trim + abs(e_offset))):
                            start_trim += b_offset
                else:
                    start_trim += b_offset

    # Adjust for user-specified offset from end of audio segment
    if end_trim > 0:  # Proceed if silence detected
        if e_offset > 0:  # If positive offset specified
            if end_trim >= e_offset:  # Apply offset if silence is long enough
                end_trim -= e_offset
        if e_offset < 0:  # If negative offset specified
            if (duration_ms - (end_trim + abs(e_offset))) > start_trim:
                end_trim += abs(e_offset)




    # Save trimmed audio segment
    my_print(v, 'Start trim w/ offset       :  {}'.format(convert_ms_to_timestring(start_trim)))
    my_print(v, 'End trim w/ offset         :  {}'.format(convert_ms_to_timestring(end_trim)))
    trimmed_sound = sound[start_trim:duration_ms-end_trim]
    my_print(v, 'New duration (m:s.ms)      :  {}'.format(convert_ms_to_timestring(len(trimmed_sound))))

    temp_file = '{}_{}.{}'.format(file_basename, starttime.strftime('%Y%m%dT%H%M%S'), file_ext)
    temp_file = os.path.join(file_location, temp_file)
    my_print(v, 'Temp file to save          :  {}'.format(temp_file))

    if not test:
        trimmed_sound.export(temp_file, format='aiff')
        send2trash(filename)
        os.rename(temp_file, filename)

    endtime = datetime.datetime.now()
    elapsed = endtime - starttime
    my_print(v, 'Script completed in        :  {}'.format(elapsed))




if __name__ == '__main__':
    main()