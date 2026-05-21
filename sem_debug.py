from __future__ import annotations

import argparse
import sys

from reporter import render
from tracer import trace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sem_debug \u2014 attribute output passages to input sources",
        epilog="Exit codes: 0=CLEAN, 1=DRIFT, 2=BLOCKED",
    )
    parser.add_argument("output_file", help="Path to the output markdown file")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=None,
        help="One or more input source markdown files",
    )
    parser.add_argument("--stage", default="", help="Stage label for the trace report")
    parser.add_argument("--threshold", type=float, default=0.35, help="Similarity threshold (default: 0.35)")
    parser.add_argument(
        "--semantic",
        action="store_true",
        default=False,
        help="Enable semantic matching via sentence-transformers on TF-IDF failures",
    )
    parser.add_argument("--report", default=None, help="Write markdown report to FILE instead of stdout")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Promote DRIFT to BLOCKED (exit code 2) when unattributed passages exist",
    )

    args = parser.parse_args()

    if not args.inputs:
        print("error: --inputs is required", file=sys.stderr)
        sys.exit(1)

    trace_result, verdict = trace(
        output_file=args.output_file,
        input_files=args.inputs,
        stage=args.stage,
        threshold=args.threshold,
        semantic=args.semantic,
    )

    if args.strict and verdict.status == "DRIFT":
        verdict.status = "BLOCKED"
        verdict.exit_code = 2

    report = render(trace_result, verdict)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        print(report)

    sys.exit(verdict.exit_code)


if __name__ == "__main__":
    main()
