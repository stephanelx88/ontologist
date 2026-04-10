from __future__ import annotations

import json
import uuid
from pathlib import Path

from pipeline.models import FraudAssessment


def _node_id(prefix: str, value: str) -> str:
    """Return a stable, unique node ID based on a prefix and value."""
    return f"{prefix}_{value}"


def generate_graph_data(assessment: FraudAssessment) -> dict:
    """Build a graphify-compatible dict (nodes + edges) from a FraudAssessment.

    Community assignments:
    - 0: Package (loan application)
    - 1: Applicant + accounts
    - 2: Employee
    - 3: Salary transactions
    - 4: Findings
    """
    pkg = assessment.package
    nodes: list[dict] = []
    edges: list[dict] = []

    # --- Package node (community 0) ---
    package_id = _node_id("package", assessment.loan_reference)
    nodes.append({
        "id": package_id,
        "label": assessment.loan_reference,
        "type": "Package",
        "community": 0,
        "properties": {
            "verdict": assessment.verdict,
            "risk_score": assessment.risk_score,
            "pages_analyzed": len(pkg.pages),
        },
    })

    # --- Applicant node (community 1) ---
    applicant_label = pkg.applicant_name or "Unknown Applicant"
    applicant_id = _node_id("applicant", applicant_label)
    nodes.append({
        "id": applicant_id,
        "label": applicant_label,
        "type": "Applicant",
        "community": 1,
        "properties": {
            "total_balance": pkg.total_balance,
        },
    })
    edges.append({
        "source": applicant_id,
        "target": package_id,
        "label": "submits",
    })

    # --- Employee node (community 2) ---
    employee_label = pkg.employee_name or "Unknown Employee"
    employee_id = _node_id("employee", pkg.employee_id or employee_label)
    nodes.append({
        "id": employee_id,
        "label": employee_label,
        "type": "Employee",
        "community": 2,
        "properties": {
            "employee_id": pkg.employee_id,
        },
    })
    edges.append({
        "source": employee_id,
        "target": package_id,
        "label": "verifies",
    })

    # --- Account nodes (community 1) ---
    for account in pkg.accounts:
        account_node_id = _node_id("account", account.number)
        nodes.append({
            "id": account_node_id,
            "label": account.number,
            "type": "Account",
            "community": 1,
            "properties": {
                "holder_name": account.holder_name,
                "balance": account.balance,
                "currency": account.currency,
                "type": account.type,
                "is_default": account.is_default,
            },
        })
        edges.append({
            "source": applicant_id,
            "target": account_node_id,
            "label": "holds account",
        })

        # --- Salary transaction nodes for this account (community 3) ---
        for txn in pkg.salary_transactions:
            txn_id = _node_id(
                "salary",
                txn.reference or f"{txn.timestamp}_{txn.amount}",
            )
            # Avoid duplicate transaction nodes (transactions aren't per-account here)
            if not any(n["id"] == txn_id for n in nodes):
                nodes.append({
                    "id": txn_id,
                    "label": txn.description or txn.reference or "Salary",
                    "type": "SalaryTransaction",
                    "community": 3,
                    "properties": {
                        "amount": txn.amount,
                        "direction": txn.direction,
                        "counterparty": txn.counterparty,
                        "timestamp": txn.timestamp,
                        "reference": txn.reference,
                    },
                })
            edges.append({
                "source": account_node_id,
                "target": txn_id,
                "label": "contains salary",
            })

    # --- Finding nodes (community 4) ---
    for finding in assessment.findings:
        finding_node_id = _node_id("finding", finding.rule_id)
        nodes.append({
            "id": finding_node_id,
            "label": finding.rule_name,
            "type": "Finding",
            "community": 4,
            "properties": {
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "description": finding.description,
                "evidence": finding.evidence,
                "page_reference": finding.page_reference,
            },
        })
        edges.append({
            "source": finding_node_id,
            "target": package_id,
            "label": "flags",
        })

    return {"nodes": nodes, "edges": edges}


def save_graph(assessment: FraudAssessment, output_dir: Path) -> Path:
    """Save graph.json to output_dir. Optionally build graph.html via graphify.

    Returns the path to the saved graph.json.
    """
    graph_data = generate_graph_data(assessment)

    output_dir.mkdir(parents=True, exist_ok=True)
    graph_path = output_dir / "graph.json"
    graph_path.write_text(
        json.dumps(graph_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    try:
        import graphify  # type: ignore[import]

        html_path = output_dir / "graph.html"
        built = graphify.build(graph_data)
        graphify.export(built, str(html_path))
    except (ImportError, Exception):
        # graphify library not available or failed — JSON output is sufficient
        pass

    return graph_path
