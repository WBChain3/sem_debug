from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import DEFAULT_THRESHOLD, Verdict
from .reporter import render, render_json
from .tracer import trace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sem_debug \u2014 attribute output passages to input sources",
        epilog="Exit codes: 0=CLEAN, 1=DRIFT, 2=BLOCKED\n"
        "\n"
        "JSON output schema (--format json or --json):\n"
        '  {\n'
        '    "status": "CLEAN|DRIFT|BLOCKED",\n'
        '    "exit_code": 0|1|2,\n'
        '    "stage": "string",\n'
        '    "threshold": float,\n'
        '    "attributed": [\n'
        '      {\n'
        '        "passage_index": int,\n'
        '        "source_file": "string",\n'
        '        "source_line_start": int,\n'
        '        "score": float,\n'
        '        "method": "tfidf|semantic"\n'
        '      }\n'
        '    ],\n'
        '    "unattributed": [\n'
        '      {\n'
        '        "passage_index": int,\n'
        '        "best_failed_score": float,\n'
        '        "text_preview": "string"\n'
        '      }\n'
        '    ]\n'
        '  }',
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
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "json"],
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Shorthand for --format json",
    )
    parser.add_argument(
        "--context-md",
        type=Path,
        default=None,
        help="Path to CONTEXT.md for section-aware input loading",
    )

    args = parser.parse_args()

    if not args.inputs and not args.context_md:
        print("error: --inputs or --context-md is required", file=sys.stderr)
        sys.exit(1)

    # --json flag overrides --format
    output_format = "json" if args.json else args.format

    trace_result, verdict = trace(
        output_file=args.output_file,
        input_files=args.inputs,
        stage=args.stage,
        threshold=args.threshold,
        semantic=args.semantic,
        context_md=args.context_md,
    )

    if args.strict and verdict.status == "DRIFT":
        verdict = Verdict(status="BLOCKED", exit_code=2)

    if output_format == "json":
        report = render_json(trace_result, verdict, args.threshold)
    else:
        report = render(trace_result, verdict)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        print(report)

    sys.exit(verdict.exit_code)


if __name__ == "__main__":
    main()
