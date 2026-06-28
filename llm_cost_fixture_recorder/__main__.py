import argparse, csv, json
from decimal import Decimal
from pathlib import Path

DEFAULT_PRICES = {"gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")), "claude-sonnet-4": (Decimal("3.00"), Decimal("15.00")), "local": (Decimal("0"), Decimal("0"))}

def estimate(rows, prices):
    total = Decimal("0")
    details = []
    for row in rows:
        model = row["model"]
        prompt = Decimal(row["prompt_tokens"])
        completion = Decimal(row["completion_tokens"])
        in_price, out_price = prices.get(model, prices["local"])
        cost = (prompt / Decimal(1_000_000) * in_price) + (completion / Decimal(1_000_000) * out_price)
        total += cost
        details.append({"name": row.get("name", model), "model": model, "cost_usd": f"{cost:.6f}"})
    return {"total_usd": f"{total:.6f}", "calls": details}

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Estimate LLM fixture costs")
    parser.add_argument("csv_file")
    parser.add_argument("--budget", type=Decimal, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = estimate(read_csv(args.csv_file), DEFAULT_PRICES)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Total: ${result['total_usd']}")
        for call in result["calls"]:
            print(f"- {call['name']}: {call['model']} ${call['cost_usd']}")
    if args.budget is not None and Decimal(result["total_usd"]) > args.budget:
        print(f"Budget exceeded: {result['total_usd']} > {args.budget}")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
