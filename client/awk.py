"""
usage: python3 awk.py <input_file_name> <output_file_name>
"""
import re
import sys

pattern = re.compile(r'sec([ 0-9.]+)MBytes')

with open(sys.argv[1], 'r') as f:
    with open(sys.argv[2], 'w') as f2:
        for line in f:
            m = pattern.search(line)
            if m:
                print(m.group(1), file=f2)
