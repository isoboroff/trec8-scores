#!/usr/bin/env python3

import argparse
import collections
from pathlib import Path

ap = argparse.ArgumentParser(
    description='Analyze the results from a GLOO experiment',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
ap.add_argument('--loo_pattern',
                help='Template for GLOO eval files',
                default='trec8-depth10/loo/eval.RUNTAG')
ap.add_argument('--loo_path',
                help='Path to GLOO eval files',
                type=Path,
                default='.')
ap.add_argument('--official_pattern',
                help='Template for official eval files',
                default='orig-summary/summary.RUNTAG.newfmt')
ap.add_argument('--official_path',
                help='Path to official eval files',
                type=Path,
                default='.')
ap.add_argument('--measures',
                help='Measures to compare, comma-seprated',
                type=lambda x: x.split(','),
                default=['map','P_10','recip_rank'])
ap.add_argument('runs_pids',
                help='List of runs and pids',
                default='runs-pids')
args = ap.parse_args()

def get_scores(runs, path, pattern):
    scores = collections.defaultdict(dict)
    for runtag in runs:
        eval_file = path / pattern.replace('RUNTAG', runtag)
        with open(eval_file, 'r') as fp:
            for line in fp:
                measure, topic, score = line.strip().split()
                if topic != 'all':
                    continue
                if not measure in args.measures:
                    continue
                scores[measure][runtag] = float(score)
    return scores

def figure_ranks(pids, official, loo):
    measures = official.keys()
    official_ranking = {}
    loo_ranking = {}
    for measure in measures:
        official_ranking[measure] = { runscore[0]: rank 
                             for rank, runscore in sorted(enumerate(official[measure].items()), 
                                                          key=lambda x: -1 * x[1][1])}
        loo_ranking[measure] = {}
        for pid in pids:
            tmp = {}
            for run in pids[pid]:
                tmp[run] = official[measure][run]
                official[measure][run] = loo[measure][run]
            new_ranking = { runscore[0]: rank
                            for rank, runscore in sorted(enumerate(official[measure].items()),
                                                         key=lambda x: -1 * x[1][1])}
            for run in pids[pid]:
                loo_ranking[measure][run] = new_ranking[run]
                official[measure][run] = tmp[run]

    return official_ranking, loo_ranking


# By Gemini 2.5 Flash, checked and corrected by me
def format_data_as_table(runtag_pid_map: dict[str, str],
                         off_score_map: dict[str, dict[str, float]],
                         off_rank_map: dict[str, dict[str, int]],
                         loo_score_map: dict[str, dict[str, float]],
                         loo_rank_map: dict[str, dict[str, int]],
                         measures: list[str]) -> str:
    """
    Formats experimental data into a human-readable table based on specified
    nested dictionary data structures.

    The table structure includes fixed 'runtag' and 'pid' columns,
    followed by groups of four columns for each 'measure' provided:
    'off score', 'off rank', 'loo score', and 'loo rank'.

    Args:
        runtag_pid_map: A dictionary where keys are runtags (str) and values are pids (str).
                        Example: {'run_A': 'p_01', 'run_B': 'p_02'}
        off_score_map: A dictionary where keys are measure names (str) and values
                       are dictionaries. The inner dictionaries have runtags (str)
                       as keys and floating-point 'off' scores as values.
                       Example: {'latency': {'run_A': 0.123, 'run_B': 0.001}, ...}
        off_rank_map: Similar to off_score_map, but with integer 'off' ranks.
        loo_score_map: Similar to off_score_map, but with floating-point 'loo' scores.
        loo_rank_map: Similar to off_score_map, but with integer 'loo' ranks.
        measures: A list of strings, where each string is a name of a 'measure'
                  (e.g., ['latency', 'throughput']). Each measure will correspond
                  to a group of four score/rank columns in the table.

    Returns:
        A multi-line string representing the formatted table.
        If data is missing for a specific (runtag, measure) pair,
        "N/A" will be displayed in the corresponding cell.
    """

    # --- Step 1: Determine optimal column widths ---
    # Calculate max width for 'runtag' and 'pid' columns based on data and headers
    max_runtag_len = len("runtag")
    max_pid_len = len("pid")

    for runtag, pid in runtag_pid_map.items():
        max_runtag_len = max(max_runtag_len, len(runtag))
        max_pid_len = max(max_pid_len, len(pid))

    # Determine widths for score and rank columns.
    # Scores are floats, formatted to 6 decimal places, e.g., "0.123456" (8 chars) or "-0.123456" (9 chars)
    # Ranks are integers.
    score_header_len = max(len("off score"), len("loo score")) # Max is 9 chars
    rank_header_len = max(len("off rank"), len("loo rank"))   # Max is 8 chars

    # Default data display width for floats (e.g., X.YYY, includes decimal)
    default_float_data_width = 5 # For "0.123"
    # Default data display width for ranks (integers)
    default_rank_data_width = 3 # Sufficient for ranks up to 999

    # Final column widths are the maximum of header length and data length requirements
    score_col_width = max(score_header_len, default_float_data_width)
    rank_col_width = max(rank_header_len, default_rank_data_width)

    # --- Step 2: Construct the table header row ---
    h1_header_parts = [
        f"{'':<{max_runtag_len + max_pid_len + 3}}",
    ]
    header_parts = [
        f"{'runtag':<{max_runtag_len}}", # Left-align runtag
        f"{'pid':<{max_pid_len}}"       # Left-align pid
    ]
    # Add headers for each measure's sub-columns
    for measure in measures:
        h1_header_parts.append(f"{measure:^{2*(score_col_width + rank_col_width + 3)+3}}")
        header_parts.append(f"{'off score':<{score_col_width}}")
        header_parts.append(f"{'off rank':<{rank_col_width}}")
        header_parts.append(f"{'loo score':<{score_col_width}}")
        header_parts.append(f"{'loo rank':<{rank_col_width}}")

    h1_header_row = " | ".join(h1_header_parts)
    header_row = " | ".join(header_parts)

    # --- Step 3: Construct the separator line for the header ---
    separator_parts = ["-" * max_runtag_len, "-" * max_pid_len]
    for _ in measures: # Add separators for each set of measure columns
        separator_parts.extend([
            "-" * score_col_width,
            "-" * rank_col_width,
            "-" * score_col_width,
            "-" * rank_col_width
        ])
    separator = "-+-".join(separator_parts)

    table_lines = [h1_header_row, header_row, separator]

    # --- Step 4: Construct data rows ---
    # Ensure consistent row order by sorting the runtags
    sorted_runtags = sorted(runtag_pid_map.keys())

    for runtag in sorted_runtags:
        # Retrieve pid for the current runtag.
        pid = runtag_pid_map.get(runtag, "") # Use .get() to handle potentially missing runtags if map is inconsistent
        row_parts = [
            f"{runtag:<{max_runtag_len}}",
            f"{pid:<{max_pid_len}}"
        ]

        # Populate score and rank data for each measure
        for measure in measures:
            # Retrieve scores and ranks using .get() with empty dicts to avoid KeyError
            # if a measure is missing, and then .get() with "N/A" for missing runtag data
            off_score = off_score_map.get(measure, {}).get(runtag, "N/A")
            off_rank = off_rank_map.get(measure, {}).get(runtag, "N/A")
            loo_score = loo_score_map.get(measure, {}).get(runtag, "N/A")
            loo_rank = loo_rank_map.get(measure, {}).get(runtag, "N/A")

            # Format data: floats to 3 decimal places, ranks as integers
            # If the value is "N/A" or another non-numeric type, convert it directly to string
            off_score_str = f"{off_score:>{score_col_width}.3f}" if isinstance(off_score, float) else f"{str(off_score):>{score_col_width}}"
            off_rank_str = f"{int(off_rank):>{rank_col_width}}" if isinstance(off_rank, (int, float)) else f"{str(off_rank):>{rank_col_width}}"
            loo_score_str = f"{loo_score:>{score_col_width}.3f}" if isinstance(loo_score, float) else f"{str(loo_score):>{score_col_width}}"
            loo_rank_str = f"{int(loo_rank):>{rank_col_width}}" if isinstance(loo_rank, (int, float)) else f"{str(loo_rank):>{rank_col_width}}"

            row_parts.extend([off_score_str, off_rank_str, loo_score_str, loo_rank_str])

        table_lines.append(" | ".join(row_parts))

    # --- Step 5: Join all lines and return the table string ---
    return "\n".join(table_lines)


# Example Usage with the new data structures:
# runtag_pid_map_example_new = {
#     'run_A': 'p_01',
#     'run_B_long': 'p_02',
#     'run_C': 'p_03_very_long',
#     'run_D': 'p_04', # Example of runtag with potentially missing measure data
# }

# measures_example_new = ['latency', 'throughput', 'error_rate']

# off_score_map_example_new = {
#     'latency': {'run_A': 0.1234567, 'run_B_long': 0.001, 'run_C': 1.0, 'run_D': 0.5},
#     'throughput': {'run_A': 0.987, 'run_B_long': 5.67, 'run_C': 2.0}, # run_D missing
#     'error_rate': {'run_A': 10.1, 'run_B_long': -0.0000001, 'run_C': 3.0},
# }

# off_rank_map_example_new = {
#     'latency': {'run_A': 1, 'run_B_long': 2, 'run_C': 3, 'run_D': 1},
#     'throughput': {'run_A': 2, 'run_B_long': 1, 'run_C': 3},
#     'error_rate': {'run_A': 3, 'run_B_long': 1, 'run_C': 2},
# }

# loo_score_map_example_new = {
#     'latency': {'run_A': 0.789, 'run_B_long': 0.111, 'run_C': 4.0}, # run_D missing
#     'throughput': {'run_A': 0.456, 'run_B_long': 0.222, 'run_C': 5.0},
#     'error_rate': {'run_A': 1.23, 'run_B_long': 0.333, 'run_C': 6.0},
# }

# loo_rank_map_example_new = {
#     'latency': {'run_A': 2, 'run_B_long': 1, 'run_C': 3}, # run_D missing
#     'throughput': {'run_A': 1, 'run_B_long': 2, 'run_C': 3},
#     'error_rate': {'run_A': 3, 'run_B_long': 1, 'run_C': 2},
# }

# formatted_table_new = format_data_as_table(
#     runtag_pid_map_example_new,
#     off_score_map_example_new,
#     off_rank_map_example_new,
#     loo_score_map_example_new,
#     loo_rank_map_example_new,
#     measures_example_new
# )
# print(formatted_table_new)


runs = {}
groups = collections.defaultdict(set)
with open(args.runs_pids, 'r') as fp:
    for line in fp:
        runtag, pid = line.strip().split()
        runs[runtag] = pid
        groups[pid].add(runtag)

# collect official scores
off_scores = get_scores(runs, args.official_path, args.official_pattern)
loo_scores = get_scores(runs, args.loo_path, args.loo_pattern)
off_ranking, loo_ranking = figure_ranks(groups, off_scores, loo_scores)
print(format_data_as_table(runs, off_scores, off_ranking, loo_scores, loo_ranking, args.measures))
