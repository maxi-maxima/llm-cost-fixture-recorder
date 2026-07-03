import argparse, csv, json
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_PRICES = {"gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")), "claude-sonnet-4": (Decimal("3.00"), Decimal("15.00")), "local": (Decimal("0"), Decimal("0"))}

def estimate(rows, prices):
    total = Decimal("0")
    details = []
    unknown_models = set()
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
        details.append({"name": row.get("name", model), "model": model, "cost_usd": f"{cost:.6f}", "priced": priced})
    return {"total_usd": f"{total:.6f}", "calls": details, "unknown_models": sorted(unknown_models)}

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

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

def main(argv=None):
    parser = argparse.ArgumentParser(description="Estimate LLM fixture costs")
    parser.add_argument("csv_file")
    parser.add_argument("--budget", type=Decimal, default=None)
    parser.add_argument("--strict-models", action="store_true", help="Fail when the CSV contains models without configured prices")
    parser.add_argument("--prices-json", help="JSON file with per-model input_per_million and output_per_million prices")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        prices = load_prices(args.prices_json) if args.prices_json else DEFAULT_PRICES
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Could not load prices: {exc}")
        return 4

    result = estimate(read_csv(args.csv_file), prices)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Total: ${result['total_usd']}")
        for call in result["calls"]:
            note = "" if call["priced"] else " (unknown price, treated as $0)"
            print(f"- {call['name']}: {call['model']} ${call['cost_usd']}{note}")
        if result["unknown_models"]:
            print(f"Unknown models: {', '.join(result['unknown_models'])}")
    if args.strict_models and result["unknown_models"]:
        print(f"Unknown model prices: {', '.join(result['unknown_models'])}")
        return 3
    if args.budget is not None and Decimal(result["total_usd"]) > args.budget:
        print(f"Budget exceeded: {result['total_usd']} > {args.budget}")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
