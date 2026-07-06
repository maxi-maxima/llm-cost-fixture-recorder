import argparse, csv, json, sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_PRICES = {"gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")), "claude-sonnet-4": (Decimal("3.00"), Decimal("15.00")), "local": (Decimal("0"), Decimal("0"))}
REQUIRED_COLUMNS = ("model", "prompt_tokens", "completion_tokens")

class CsvInputError(ValueError):
    pass

def estimate(rows, prices):
    total = Decimal("0")
    details = []
    unknown_models = set()
    totals_by_model = {}
    for row in rows:
        model = row["model"]
        prompt = Decimal(row["prompt_tokens"])
        completion = Decimal(row["completion_tokens"])
        if model in prices:
            in_price, out_price = prices[model]
            priced = True
        else:
            in_price, out_price = prices["local"]
            priced = False
            unknown_models.add(model)
        cost = (prompt / Decimal(1_000_000) * in_price) + (completion / Decimal(1_000_000) * out_price)
        total += cost
        summary = totals_by_model.setdefault(model, {"model": model, "prompt_tokens": Decimal("0"), "completion_tokens": Decimal("0"), "cost_usd": Decimal("0"), "priced": priced})
        summary["prompt_tokens"] += prompt
        summary["completion_tokens"] += completion
        summary["cost_usd"] += cost
        summary["priced"] = summary["priced"] and priced
        details.append({"name": row.get("name", model), "model": model, "cost_usd": f"{cost:.6f}", "priced": priced})
    model_totals = []
    for model in sorted(totals_by_model):
        summary = totals_by_model[model]
        model_totals.append({
            "model": model,
            "prompt_tokens": str(summary["prompt_tokens"]),
            "completion_tokens": str(summary["completion_tokens"]),
            "cost_usd": f"{summary['cost_usd']:.6f}",
            "priced": summary["priced"],
        })
    return {"total_usd": f"{total:.6f}", "calls": details, "model_totals": model_totals, "unknown_models": sorted(unknown_models)}

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        missing = [name for name in REQUIRED_COLUMNS if name not in fieldnames]
        if missing:
            raise CsvInputError(f"missing required columns: {', '.join(missing)}")
        rows = list(reader)
    for row_number, row in enumerate(rows, start=2):
        for column in ("prompt_tokens", "completion_tokens"):
            value = row.get(column, "")
            try:
                Decimal(value)
            except (InvalidOperation, TypeError):
                raise CsvInputError(f"row {row_number} has invalid {column} value: {value}") from None
    return rows

def load_prices(path):
    prices = dict(DEFAULT_PRICES)
    with Path(path).open(encoding="utf-8") as fh:
        payload = json.load(fh)
    for model, value in payload.items():
        try:
            in_price = Decimal(str(value["input_per_million"]))
            out_price = Decimal(str(value["output_per_million"]))
        except (KeyError, TypeError, InvalidOperation) as exc:
            raise ValueError(f"invalid price entry for {model!r}") from exc
        prices[model] = (in_price, out_price)
    return prices

def write_model_totals_csv(path, model_totals):
    fieldnames = ["model", "prompt_tokens", "completion_tokens", "cost_usd", "priced"]
    if path == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(model_totals)
        return
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(model_totals)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Estimate LLM fixture costs")
    parser.add_argument("csv_file")
    parser.add_argument("--budget", type=Decimal, default=None)
    parser.add_argument("--warn-budget", type=Decimal, default=None, help="Print a warning when total cost exceeds this soft budget without failing the command")
    parser.add_argument("--strict-models", action="store_true", help="Fail when the CSV contains models without configured prices")
    parser.add_argument("--prices-json", help="JSON file with per-model input_per_million and output_per_million prices")
    parser.add_argument("--model-totals-csv", help="Write per-model token and cost totals to a CSV file; use '-' for stdout")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        prices = load_prices(args.prices_json) if args.prices_json else DEFAULT_PRICES
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Could not load prices: {exc}")
        return 4

    try:
        result = estimate(read_csv(args.csv_file), prices)
    except (CsvInputError, OSError) as exc:
        print(f"Invalid CSV input: {exc}")
        return 5
    warn_exceeded = args.warn_budget is not None and Decimal(result["total_usd"]) > args.warn_budget
    result["warn_budget_usd"] = f"{args.warn_budget:.6f}" if args.warn_budget is not None else None
    result["warn_budget_exceeded"] = warn_exceeded
    if args.model_totals_csv and args.model_totals_csv != "-":
        try:
            write_model_totals_csv(args.model_totals_csv, result["model_totals"])
        except OSError as exc:
            print(f"Could not write model totals CSV: {exc}")
            return 6
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Total: ${result['total_usd']}")
        for call in result["calls"]:
            note = "" if call["priced"] else " (unknown price, treated as $0)"
            print(f"- {call['name']}: {call['model']} ${call['cost_usd']}{note}")
        if len(result["model_totals"]) > 1:
            print("By model:")
            for model in result["model_totals"]:
                note = "" if model["priced"] else " (unknown price, treated as $0)"
                print(f"- {model['model']}: ${model['cost_usd']} ({model['prompt_tokens']} prompt, {model['completion_tokens']} completion tokens){note}")
        if result["unknown_models"]:
            print(f"Unknown models: {', '.join(result['unknown_models'])}")
        if warn_exceeded:
            print(f"Budget warning: {result['total_usd']} > {args.warn_budget}")
    if args.model_totals_csv == "-":
        write_model_totals_csv("-", result["model_totals"])
    if args.strict_models and result["unknown_models"]:
        print(f"Unknown model prices: {', '.join(result['unknown_models'])}")
        return 3
    if args.budget is not None and Decimal(result["total_usd"]) > args.budget:
        print(f"Budget exceeded: {result['total_usd']} > {args.budget}")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
