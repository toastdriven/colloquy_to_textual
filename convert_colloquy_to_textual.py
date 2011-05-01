from dateutil.parser import parse
import glob
from lxml import etree
from lxml import objectify
import os
import sys


__author__ = 'Daniel Lindsley'
__version__ = (0, 2, 0)
__license__ = 'New BSD'


# Approach:
# - Glob the transcripts
# - Create the "converted" directory
# - Per transcript:
#   - Read the file
#   - Load it with lxml
#   - Open the file to write to
#   - Iterate over the messages
#     - Parse them, yanking out the details
#     - Write the revised version to the new log file.


class ColloquyConvertor(object):
    message_format = u"[%(month)02d/%(day)02d/%(year)4d -:- %(hour)02d:%(minute)02d:%(second)02d %(ampm)s] %(nick)s: %(message)s\n"
    event_format = u"[%(month)02d/%(day)02d/%(year)4d -:- %(hour)02d:%(minute)02d:%(second)02d %(ampm)s] %(event)s\n"
    
    def __init__(self, directory_path, network='irc.freenode.net'):
        self.colloquy_dir = directory_path
        self.converted_path = os.path.join(directory_path, 'converted')
        self.network = network
    
    def get_transcript_list(self):
        path = os.path.join(self.colloquy_dir, '*.colloquyTranscript')
        return glob.glob(path)
    
    def get_private_list(self):
        path = os.path.join(self.colloquy_dir, self.network, '*.colloquyTranscript')
        return glob.glob(path)
    
    def read_file(self, filename):
        log_file = open(filename, 'r')
        return objectify.parse(log_file)
    
    def get_new_transcript_path(self, old_transcript_filename):
        channel_details, ext = os.path.splitext(os.path.basename(old_transcript_filename))
        channel_name, date = channel_details.split(' ')
        channels_dir = os.path.join(self.converted_path, 'Channels')
        channel_dir = os.path.join(channels_dir, channel_name)
        
        if not os.path.exists(channels_dir):
            os.mkdir(channels_dir)
        
        if not os.path.exists(channel_dir):
            os.mkdir(channel_dir)
        
        month, day, year = date.split('-')
        log_filename = "20%02d-%02d-%02d.txt" % (int(year), int(month), int(day))
        return os.path.join(channel_dir, log_filename)
    
    def get_new_private_path(self, old_private_filename):
        nick_details, ext = os.path.splitext(os.path.basename(old_private_filename))
        nick, date = nick_details.split(' ')
        queries_dir = os.path.join(self.converted_path, 'Queries')
        query_dir = os.path.join(queries_dir, nick)
        
        if not os.path.exists(queries_dir):
            os.mkdir(queries_dir)
        
        if not os.path.exists(query_dir):
            os.mkdir(query_dir)
        
        month, day, year = date.split('-')
        log_filename = "20%02d-%02d-%02d.txt" % (int(year), int(month), int(day))
        return os.path.join(query_dir, log_filename)
    
    def clean_message(self, element):
        etree.strip_tags(element, 'span', 'samp', 'a')
        return element
    
    def parse_envelope(self, element):
        message_data = []
        nick = element.sender.text
        
        for message in element.message:
            date = parse(message.get('received'))
            ampm = 'AM'
            
            if date.hour >= 12:
                ampm = 'PM'
            
            clean_message = self.clean_message(message)
            message_data.append({
                'year': date.year,
                'month': date.month,
                'day': date.day,
                'hour': date.hour,
                'minute': date.minute,
                'second': date.second,
                'ampm': ampm,
                'nick': nick,
                'message': clean_message.text,
            })
        
        return message_data
    
    def parse_event(self, element):
        date = parse(element.get('occurred'))
        ampm = 'AM'
        
        if date.hour >= 12:
            ampm = 'PM'
        
        clean_message = self.clean_message(element.message)
        return {
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'hour': date.hour,
            'minute': date.minute,
            'second': date.second,
            'ampm': ampm,
            'event': clean_message.text,
        }
    
    def write_updated(self, old_log, new_transcript_path):
        new_log_file = open(new_transcript_path, 'w')
        log = old_log.getroot()
        
        for element in log.iterchildren():
            if element.tag == 'envelope':
                message_data = self.parse_envelope(element)
                
                for data in message_data:
                    message = self.message_format % data
                    new_log_file.write(message.encode('utf-8'))
            elif element.tag == 'event':
                event_data = self.parse_event(element)
                event = self.event_format % event_data
                new_log_file.write(event.encode('utf-8'))
            else:
                print "Saw unrecognized tag '%s'. Continuing..." % element.tag
    
    def run(self):
        if not os.path.exists(self.converted_path):
            os.mkdir(self.converted_path)
        
        transcripts = self.get_transcript_list()
        privates = self.get_private_list()
        
        for transcript_filename in transcripts:
            old_log = self.read_file(transcript_filename)
            new_transcript_path = self.get_new_transcript_path(transcript_filename)
            self.write_updated(old_log, new_transcript_path)
        
        for private_filename in privates:
            old_log = self.read_file(private_filename)
            new_private_path = self.get_new_private_path(private_filename)
            self.write_updated(old_log, new_private_path)


if __name__ == '__main__':
    if not len(sys.argv) == 2:
        print "Usage: %s <colloquy_path>"
        sys.exit(1)
    
    cc = ColloquyConvertor(directory_path=sys.argv[1])
    cc.run()
