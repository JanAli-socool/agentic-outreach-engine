"""Batch eval runner. Measures ICP classification accuracy."""
import json
from rich import print
from rich.table import Table
from agent.graph import build_graph
from agent.state import AgentState


ICP = (
    "B2B SaaS company, 10 to 300 employees, focused on AI, developer tools, "
    "or data infrastructure. Based in US, Canada, or Europe."
)


def main():
    with open("evals/dataset.jsonl", "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    graph = build_graph()
    results = []

    for case in cases:
        domain = case["domain"]
        expected = case["expected_fit"]

        state = AgentState(company_domain=domain, icp_criteria=ICP)
        try:
            result_dict = graph.invoke(state)
            result = AgentState(**result_dict) if isinstance(result_dict, dict) else result_dict
            predicted = result.icp_decision.is_fit if result.icp_decision else None
            confidence = result.icp_decision.confidence if result.icp_decision else 0.0
            status = result.status
        except Exception as e:
            predicted = None
            confidence = 0.0
            status = f"error: {e}"

        correct = predicted == expected
        results.append({
            "domain": domain,
            "expected": expected,
            "predicted": predicted,
            "confidence": confidence,
            "correct": correct,
            "status": status,
        })

    table = Table(title="ICP Classification Eval Results")
    table.add_column("Domain")
    table.add_column("Expected")
    table.add_column("Predicted")
    table.add_column("Confidence")
    table.add_column("Correct")
    table.add_column("Status")

    for r in results:
        table.add_row(
            r["domain"],
            str(r["expected"]),
            str(r["predicted"]),
            f"{r['confidence']:.2f}",
            "✓" if r["correct"] else "✗",
            r["status"],
        )

    print(table)

    valid = [r for r in results if r["predicted"] is not None]
    if valid:
        accuracy = sum(1 for r in valid if r["correct"]) / len(valid)
        print(f"\n[bold green]Accuracy:[/bold green] {accuracy:.1%} ({sum(1 for r in valid if r['correct'])}/{len(valid)})")
    else:
        print("[bold red]No valid predictions.[/bold red]")


if __name__ == "__main__":
    main()