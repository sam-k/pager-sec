#!/usr/bin/env python3

import csv
import os
import sys
from collections import OrderedDict
from datetime import datetime
from hashlib import sha256


MAX_KEEP = 10  # how many entries to keep track of simultaneously
HASH_OUTPUT = True  # hash sensitive output?

TIMESTAMP = datetime.timestamp(datetime.now())
DIRNAME = os.path.dirname(__file__)
LOG_FILE = os.path.join(DIRNAME, f"output/out_{TIMESTAMP}.txt")
CSV_FILE = os.path.join(DIRNAME, f"output/out_{TIMESTAMP}.csv")


def split_line(line: str):
    """
    Splits a multimon-ng output line into its fields.

    Args:
        line: Output line from multimon-ng
    Returns:
        Array of fields
    """

    fields = line.split("|", 7)
    if len(fields) < 7:  # probably some header
        return None

    if fields[6] == "ALN":  # alphanumerics have an extra field before msg
        temp = fields[-1].split("|")
        fields = fields[:-1]
        fields.extend(temp)

    return fields


def print_log(f, metadata: list, msg: str, msg_id: int):
    """
    Prints a compiled message.

    Args:
        f: File descriptor
        metadata: Metadata fields of an output line
        msg: Compiled message
        msg_id: Unique ID for message
    """

    if HASH_OUTPUT:
        msg = sha256(msg.encode("utf-8")).hexdigest()
    for md in metadata:
        f.write(f'{"|".join(md)}\n')
    f.write(f"└─ {msg}\n\n")


def print_csv(w, metadata: list, msg: str, msg_id: int):
    """
    Writes a compiled message into a CSV file.

    Args:
        w: CSV writer
        metadata: Metadata fields of an output line
        msg: Compiled message
        msg_id: Unique ID for message
    """

    if HASH_OUTPUT:
        msg = sha256(msg.encode("utf-8")).hexdigest()
    for md in metadata:
        frame_info = md[2].split(".")
        addr_type = list(md[4])
        frag_info = md[7].split(".") if len(md) >= 8 else [""] * 3
        w.writerow(
            [
                md[0],  # protocol
                md[1],  # transmission
                int(frame_info[0]),  # frame_cycle
                int(frame_info[1]),  # frame_num
                frame_info[2],  # frame_phase
                md[3],  # capcode
                *addr_type,  # address_ls, address_gs
                md[6],  # page_type
                *frag_info,  # frag_indicator, frag_cont, frag_flag
                msg,  # message
                msg_id,  # message_id
            ]
        )


def main():
    """
    Main.
    """

    # OrderedDict of {capcode : [[metadata], msg, msg_hash]}
    cc_dict = OrderedDict()
    # Message ID
    msg_id = 0

    with open(LOG_FILE, "a") as f_log, open(CSV_FILE, "a") as f_csv:
        try:
            csv_writer = csv.writer(f_csv, delimiter=",", quotechar='"')
            csv_writer.writerow(
                [
                    "protocol",
                    "transmission",
                    "frame_cycle",
                    "frame_num",
                    "frame_phase",
                    "capcode",
                    "address_ls",
                    "address_gs",
                    "page_type",
                    "frag_indicator",
                    "frag_cont",
                    "frag_flag",
                    "message",
                    "message_id",
                ]
            )

            for line in sys.stdin:
                fields = split_line(line)
                if not fields:
                    continue

                cc = fields[3]  # capcode
                page_type = fields[6]
                frag_flag = fields[7].split(".")[2] if page_type == "ALN" else None

                metadata = fields[:-1]
                if HASH_OUTPUT:
                    metadata[3] = sha256(cc.encode("utf-8")).hexdigest()
                msg = fields[-1].strip()

                if not frag_flag or frag_flag == "K":  # 1st and only frag
                    print_log(f_log, [metadata], msg, msg_id)
                    print_csv(csv_writer, [metadata], msg, msg_id)
                    msg_id += 1
                else:  # more frags to follow, or last frag
                    if cc in cc_dict:  # shouldn't happen for frag_flag == "C"
                        cc_dict[cc][0].append(metadata)
                        cc_dict[cc][1] += msg
                    else:
                        cc_dict[cc] = [[metadata], msg, msg_id]
                        msg_id += 1

                    if frag_flag == "C":  # last frag
                        pop_data = cc_dict.pop(cc)
                        print_log(f_log, *pop_data)
                        print_csv(csv_writer, *pop_data)

                # If cc_dict is getting too long, evict until down to MAX_KEEP size
                while len(cc_dict) > MAX_KEEP:
                    _, pop_data = cc_dict.popitem(last=False)
                    print_log(f_log, *pop_data)
                    print_csv(csv_writer, *pop_data)

        # If quit unexpectedly, dump cc_dict
        except KeyboardInterrupt:
            while cc_dict:
                _, pop_data = cc_dict.popitem(last=False)
                print_log(f_log, *pop_data)
                print_csv(csv_writer, *pop_data)


if __name__ == "__main__":
    main()
