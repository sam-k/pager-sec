#!/usr/bin/env python3

import os
import sys
from collections import deque
from datetime import datetime


TIMEOUT = 10
DIRNAME = os.path.dirname(__file__)
LOG_FILE = os.path.join(DIRNAME, f"flex_{datetime.timestamp(datetime.now())}.txt")


def main():
    # Queue of capcodes (max # = TIMEOUT)
    cc_q = deque([None] * TIMEOUT)
    # Dict of {capcode : [[metadata], msg, msg_hash]}
    cc_dict = {}

    with open(LOG_FILE, "a") as f:
        for line in sys.stdin:
            fields = line.split("|", 7)
            if len(fields) < 7:  # probably some header
                continue

            cc = fields[3]  # capcode
            if fields[6] == "ALN":  # alphanumerics have an extra field before msg
                temp = fields[-1].split("|")
                fields = fields[:-1]
                fields.extend(temp)
            metadata = "|".join(fields[:-1])
            msg = fields[-1].strip()

            # Concatenate data if capcodes are the same
            if cc in cc_dict:
                cc_q.append(None)
                cc_dict[cc][0].append(metadata)
                cc_dict[cc][1] += msg
                cc_dict[cc][2] = hash(cc_dict[cc][1])
            else:
                cc_q.append(cc)
                cc_dict[cc] = [[metadata], msg, hash(msg)]

            # Pop queue to print data
            this_cc = cc_q.popleft()
            if this_cc and this_cc in cc_dict:
                for md in cc_dict[this_cc][0]:
                    f.write(f"{md}\n")
                f.write(f"└─ {cc_dict[this_cc][1]}\n\n")
                del cc_dict[this_cc]


if __name__ == "__main__":
    main()
