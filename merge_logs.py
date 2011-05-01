from dateutil.parser import parse
import glob
import os
import re
import sys


LINE_RE = re.compile(r'^\[(?P<date>.*?)\] (?P<message>.*)')


def unshift(mr_list):
    try:
        return mr_list.pop(0)
    except IndexError:
        return None


def rip_apart(line):
    match = LINE_RE.search(line)
    
    if match:
        matched = match.groupdict()
        date = parse(matched['date'].replace('-:-', '-'))
        return date, matched['message']
    
    return None, line


def dance(logfile):
    line = unshift(logfile)
    
    if not line:
        return None, None, None
    
    line_date, line_message = rip_apart(line)
    return line, line_date, line_message


def combine_files(file_1, file_2):
    logfile_1 = open(file_1, 'r').readlines()
    logfile_2 = open(file_2, 'r').readlines()
    write_file = open(file_1, 'w')
    
    line_1, line_1_date, line_1_message = dance(logfile_1)
    line_2, line_2_date, line_2_message = dance(logfile_2)
    
    while line_1 and line_2:
        if line_1_message == line_2_message:
            write_file.write(line_1)
            # Unshift both, since they were the same message.
            line_1, line_1_date, line_1_message = dance(logfile_1)
            line_2, line_2_date, line_2_message = dance(logfile_2)
            continue
        
        if line_1_date < line_2_date:
            write_file.write(line_1)
            line_1, line_1_date, line_1_message = dance(logfile_1)
        else:
            write_file.write(line_2)
            line_2, line_2_date, line_2_message = dance(logfile_2)
    
    # Once we get here, we've exhausted one of the other. Write what's left.
    if len(logfile_1):
        for line in logfile_1:
            write_file.write(line)
    
    if len(logfile_2):
        for line in logfile_2:
            write_file.write(line)
    
    write_file.close()


def build_file_list(directory):
    return glob.glob(os.path.join(directory, '*/*/*.txt'))


def run(merge_dir, extra_dir):
    import pdb; pdb.set_trace()
    extra_files = build_file_list(extra_dir)
    
    for extra_file in extra_files:
        possible_merge_file = extra_file.replace(extra_dir, merge_dir)
        
        if os.path.exists(possible_merge_file):
            print "Working on '%s'..." % possible_merge_file.replace(merge_dir, '')
            combine_files(possible_merge_file, extra_file)


if __name__ == '__main__':
    if not len(sys.argv) == 3:
        print "Usage: python merge_logs.py <master_directory/irc.freenode.net> <extra_directory/irc.freenode.net>"
        sys.exit(1)
    
    run(sys.argv[1], sys.argv[2])
