#!/usr/bin/env python3

from collections import deque
import random
import string
import time

# Weighted dict of page header choices.
PARAMS = {
    "protocol": (("FLEX", "POCSAG512", "POCSAG1200", "POCSAG2400"), (1, 0, 0, 0)),
    "transmit": (("1600/2", "3200/2", "3200/4", "6400/4"), (0, 0, 1, 0)),
    "frame_phase": {
        "1600/2": (("A"), (1)),
        "3200/2": (("A", "C"), (1, 1)),
        "3200/4": (("A", "C"), (1, 1)),
        "6400/4": (("A", "B", "C", "D"), (1, 1, 1, 1)),
    },
    "addr_ls": (("L", "S"), (24, 1)),
    "addr_gs": (("G", "S"), (1, 199)),
    "page_type": (("TON", "NUM", "ALN", "BIN"), (9, 20, 70, 1)),
    "multi_frag": ((True, False), (1, 3)),
    "cont_frag": ((True, False), (1, 1)),
    "gen_new": ((True, False), (1, 4)),
}
PAGE_ENUMS = {"TON": 2, "NUM": 3, "ALN": 5, "BIN": 6}
MSG_SPACE = {
    "TON": string.digits,
    "NUM": string.digits,
    "ALN": string.ascii_letters + string.digits + " ",
    "BIN": string.digits,
}


def generate_header_comps():
    protocol = random.choices(PARAMS["protocol"][0], PARAMS["protocol"][1], k=1)[0]
    transmit = random.choices(PARAMS["transmit"][0], PARAMS["transmit"][1], k=1)[0]
    frame_phase = random.choices(
        PARAMS["frame_phase"][transmit][0],
        PARAMS["frame_phase"][transmit][1],
        k=1,
    )[0]
    capcode = str(random.randint(0, 9999999)).zfill(10)
    addr_ls = random.choices(PARAMS["addr_ls"][0], PARAMS["addr_ls"][1], k=1)[0]
    addr_gs = random.choices(PARAMS["addr_gs"][0], PARAMS["addr_gs"][1], k=1)[0]
    page_type = random.choices(PARAMS["page_type"][0], PARAMS["page_type"][1], k=1)[0]
    page_enum = PAGE_ENUMS[page_type]

    return {
        "protocol": protocol,
        "transmit": transmit,
        "frame_phase": frame_phase,
        "capcode": capcode,
        "addr_type": f"{addr_ls}{addr_gs}",
        "page_type": page_type,
        "page_enum": page_enum,
    }


def build_header(header_comps, cycle_num, frame_num, frag_info=None):
    cycle_str = str(cycle_num).zfill(2)
    frame_str = str(frame_num).zfill(3)
    header = f'{header_comps["protocol"]}|{header_comps["transmit"]}|{cycle_str}.{frame_str}.{header_comps["frame_phase"]}|{header_comps["capcode"]}|{header_comps["addr_type"]}|{header_comps["page_enum"]}|{header_comps["page_type"]}'
    if frag_info:
        header += f"|{frag_info}"
    return header


def generate_msg(page_type, length=None, range=(1, 100)):
    return "".join(
        random.choices(
            MSG_SPACE[page_type],
            k=(random.randint(*range) if length is None else length),
        )
    )


def main():
    # Initialize params.
    cycle_num = random.randint(0, 14)
    frame_num = random.randint(0, 127)

    # Queue of saved headers for ALN message fragments.
    # (header, frag_ind)
    saved_headers = deque()

    # Generate random pages.
    while True:
        frame_num += 1
        if frame_num >= 128:
            cycle_num = (cycle_num + 1) % 15
            frame_num %= 128

        # If there are headers saved, generate the next fragment 75% of the time.
        if (
            saved_headers
            and random.choices(PARAMS["gen_new"][0], PARAMS["gen_new"][1], k=1)[0]
        ):
            header_comps = saved_headers.popleft()
            # End or continue current message.
            if random.choices(PARAMS["cont_frag"][0], PARAMS["cont_frag"][1], k=1)[0]:
                frag_info = f'{header_comps["frag_ind"]}.1.F'
                header_comps["frag_ind"] += 2 if header_comps["frag_ind"] == 2 else 1
                saved_headers.append(header_comps)
            else:
                frag_info = f'{header_comps["frag_ind"]}.0.C'
            header = build_header(header_comps, cycle_num, frame_num, frag_info)
            print(f'{header}|{generate_msg("ALN")}')
        # Else, generate a new message.
        else:
            header_comps = generate_header_comps()
            msg = generate_msg(header_comps["page_type"])

            if header_comps["page_type"] == "ALN":
                if random.choices(
                    PARAMS["multi_frag"][0], PARAMS["multi_frag"][1], k=1
                )[0]:
                    frag_info = "3.1.F"
                    header_comps["frag_ind"] = 0
                    saved_headers.append(header_comps)
                else:
                    frag_info = "3.0.K"
                header = build_header(header_comps, cycle_num, frame_num, frag_info)
            else:
                header = build_header(header_comps, cycle_num, frame_num)
            print(f"{header}|{msg}")
        time.sleep(random.uniform(0, 3))


if __name__ == "__main__":
    main()
