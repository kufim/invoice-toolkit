import argparse
from pathlib import Path

from . import processor


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="invoice-process",
        description="Read a folder of invoice PDFs into a CSV and a summary report.",
    )
    parser.add_argument("folder", help="folder containing invoice PDFs")
    parser.add_argument("-o", "--output", default="invoices.csv", help="output CSV path")
    parser.add_argument("-r", "--report", default="report.txt", help="output report path")
    args = parser.parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        parser.error(f"not a folder: {folder}")

    records = processor.process_folder(folder)
    if not records:
        print("No PDFs found.")
        return 1

    processor.write_csv(records, args.output)
    report = processor.build_report(records)
    processor.write_report(report, args.report)

    print(f"Processed {len(records)} invoices -> {Path(args.output).resolve()}")
    print()
    print(processor.format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())