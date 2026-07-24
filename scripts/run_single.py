"""CLI: run agent on a single company domain."""
import sys
from rich import print
from rich.panel import Panel
from agent.graph import build_graph
from agent.state import AgentState


DEFAULT_ICP = (
    "B2B SaaS company, 10 to 300 employees, focused on AI, developer tools, "
    "or data infrastructure. Based in US, Canada, or Europe. Shows signs of "
    "active product development and growth (hiring, recent launches, funding)."
)


def main():
    if len(sys.argv) < 2:
        print("[bold red]Usage:[/bold red] python scripts/run_single.py <domain> [icp_criteria]")
        sys.exit(1)

    domain = sys.argv[1]
    icp = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_ICP

    print(Panel(f"[bold]Running agent on:[/bold] {domain}", style="cyan"))

    graph = build_graph()
    initial = AgentState(company_domain=domain, icp_criteria=icp)
    result_dict = graph.invoke(initial, {"recursion_limit": 50})
    result = AgentState(**result_dict) if isinstance(result_dict, dict) else result_dict

    print(Panel("[bold]TRACE[/bold]", style="yellow"))
    for line in result.trace:
        print(f"  {line}")

    print(Panel(f"[bold]STATUS:[/bold] {result.status}", style="green" if result.status == "completed" else "red"))

    if result.icp_decision:
        print(Panel("[bold]ICP DECISION[/bold]", style="magenta"))
        print(result.icp_decision.model_dump())

    if result.email_draft:
        print(Panel("[bold]EMAIL DRAFT[/bold]", style="blue"))
        print(f"[bold]Subject:[/bold] {result.email_draft.subject}")
        print(f"[bold]Body:[/bold]\n{result.email_draft.body}")
        print(f"[bold]Hooks:[/bold] {result.email_draft.personalization_hooks}")

    if result.verification:
        print(Panel("[bold]VERIFICATION[/bold]", style="yellow"))
        print(result.verification.model_dump())

    if result.error:
        print(Panel(f"[bold red]ERROR:[/bold red] {result.error}", style="red"))


if __name__ == "__main__":
    main()