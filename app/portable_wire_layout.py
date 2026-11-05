"""Transport wire limits shared by Python validation and generated Swift guard."""
import hashlib
from pathlib import Path
MAX_INPUT_WORDS=131072
LARGE_OUTPUT_WORDS=(655360,786432,806912,1048576,1310720,1507328,1769472,1769856,2032000,2048912,2064786,2165136,2345384,2362296,2395112,2558208,2691344,2871592,2912552,2945320,2962232,2995048,10422672)
MAX_OUTPUT_WORDS=max(LARGE_OUTPUT_WORDS)


def check_output_words(output_words):
    """Common native/WASM output-stride bounds; no device adapter dependency."""
    if type(output_words) is not int or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in LARGE_OUTPUT_WORDS:
        raise ValueError('Unsupported output word stride')
    return output_words
