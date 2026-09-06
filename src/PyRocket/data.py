"""CSV adapters shared by batch and importable analysis."""
import csv


def read_curve(args):
    if args.limit is not None and args.limit < 2:
        raise ValueError("limit must be at least two")
    time, thrust = [], []
    with args.input.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(c not in reader.fieldnames for c in [args.time_column, args.thrust_column]):
            raise ValueError("CSV must contain the requested time and thrust columns")
        for row in reader:
            try:
                time.append(float(row[args.time_column]))
                thrust.append(float(row[args.thrust_column]) * (4.4482216152605 if args.thrust_unit == "lbf" else 1))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid numeric sample at CSV line {reader.line_num}") from exc
            if args.limit is not None and len(time) >= args.limit:
                break
    return time, thrust
