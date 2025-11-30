from pathlib import Path
import json
import pytest
import traceback
from google.adk.evaluation.agent_evaluator import AgentEvaluator, EvalConfig, BaseCriterion
from google.adk.evaluation.eval_set import EvalSet  # still used for the path, but not strictly needed

EVAL_DIR = "./Scripts/evals"
EVAL_RESULT_DIR = "./tests/results"
 # --- ensure output dir ---
output_dir = Path(EVAL_RESULT_DIR)
output_dir.mkdir(parents=True, exist_ok=True)

@pytest.mark.asyncio
async def test_with_single_test_file():
    """Test the agent's basic ability via a session file."""

    eval_config = EvalConfig(
        criteria={
            "tool_trajectory_avg_score": BaseCriterion(threshold=0.95),
            "response_match_score": BaseCriterion(threshold=0.5),
        }
    )

    # Path to your evalset file
    path = Path(EVAL_DIR) / "evalset_complete_happypath.evalset.json"

    try:
        # === Run eval using the 1.19-style API ===
        eval_results = await AgentEvaluator.evaluate(
            agent_module="mortgage_deposit_agent",
            eval_dataset_file_path_or_dir=str(path),
            # eval_config=eval_config,
            num_runs=1,
            print_detailed_results=True,
        )
    except Exception as e:
        # ✅ Always write an error report if evaluation explodes
        error_payload = {
            "error_type": type(e).__name__,
            "error_str": str(e),
            "traceback": traceback.format_exc(),
        }
        (output_dir / "eval_error.json").write_text(
            json.dumps(error_payload, indent=2),
            encoding="utf-8",
        )
        # Let pytest still see the failure
        raise
    

    # We only passed one file, so take the first EvalSetResult
    eval_set_result = eval_results[0]
    # Dump raw result
    try:
        result_dict = eval_set_result.model_dump()
    except AttributeError:
        result_dict = eval_set_result.dict()

    (output_dir / "eval_output.json").write_text(
        json.dumps(result_dict, indent=2),
        encoding="utf-8",
    )
   

    # ---- Save raw result JSON ----
    # Pydantic v2: model_dump(); if that errors, try .dict()
    try:
        result_dict = eval_set_result.model_dump()
    except AttributeError:
        result_dict = eval_set_result.dict()

    with open(output_dir / "eval_output.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    # ---- Build a summary ----
    summary = {
        "overall_status": eval_set_result.overall_status.name,
        "overall_metrics": {},  # aggregated per metric across all invocations
        "cases": [],
    }

    # First, aggregate per-metric stats across all cases/invocations
    from collections import defaultdict

    metric_acc = defaultdict(list)  # metric_name -> list[(score, threshold, status)]

    for case in eval_set_result.eval_case_results:
        for mr in case.eval_metric_result_per_invocation:
            metric_acc[mr.metric_name].append(
                (mr.score, mr.threshold, mr.eval_status.name)
            )

    for metric_name, values in metric_acc.items():
        scores = [s for s, _, _ in values]
        thresholds = {t for _, t, _ in values}
        statuses = [st for _, _, st in values]
        avg_score = sum(scores) / len(scores) if scores else None
        # assume same threshold for all invocations of a metric
        threshold = thresholds.pop() if thresholds else None
        overall_status = "PASSED" if all(st == "PASSED" for st in statuses) else "FAILED"

        summary["overall_metrics"][metric_name] = {
            "score": avg_score,
            "threshold": threshold,
            "status": overall_status,
        }

    # Per-eval-case details
    for case in eval_set_result.eval_case_results:
        case_entry = {
            "eval_id": case.eval_id,
            "status": case.overall_status.name,
            "metrics": {},
        }
        for mr in case.eval_metric_result_per_invocation:
            case_entry["metrics"][mr.metric_name] = {
                "score": mr.score,
                "threshold": mr.threshold,
                "status": mr.eval_status.name,
            }
        summary["cases"].append(case_entry)

    # Save summary JSON
    with open(output_dir / "eval_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Save HTML report
    await save_as_html(output_dir, summary)

    # Print some nice console output
    print("\n--- ✅ EVAL RESULTS ---")
    print(f"Overall status: {summary['overall_status']}")
    for metric_name, data in summary["overall_metrics"].items():
        print(
            f"  [Overall] {metric_name}: "
            f"Score={data['score']:.3f}  Threshold={data['threshold']:.3f}  Status={data['status']}"
        )

    # Keep the assertion behaviour for pytest
    assert eval_set_result.overall_status.is_pass, "Eval failed – see eval_output.json"


async def save_as_html(output_dir: Path, summary: dict):
    status = summary["overall_status"]
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; margin: 40px; }}
            table {{ border-collapse: collapse; margin-bottom: 30px; width: 80%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; }}
            th {{ background-color: #eee; }}
            .status-PASSED {{ background-color: #c8f7c5; }}
            .status-FAILED {{ background-color: #f7c5c5; }}
        </style>
    </head>
    <body>
    <h1>ADK Evaluation Report</h1>
    <h2>Overall Status: <span class="status-{status}">{status}</span></h2>
    <h3>Overall Metrics</h3>
    <table>
        <tr><th>Metric</th><th>Score</th><th>Threshold</th><th>Status</th></tr>
    """

    for metric, data in summary["overall_metrics"].items():
        html += f"""
        <tr class="status-{data['status']}">
            <td>{metric}</td>
            <td>{data['score']}</td>
            <td>{data['threshold']}</td>
            <td>{data['status']}</td>
        </tr>
        """

    html += "</table><h3>Test Cases</h3>"

    for case in summary["cases"]:
        html += f"""
        <h4>Case: {case['eval_id']} — <span class="status-{case['status']}">{case['status']}</span></h4>
        <table>
            <tr><th>Metric</th><th>Score</th><th>Threshold</th><th>Status</th></tr>
        """
        for metric, data in case["metrics"].items():
            html += f"""
            <tr class="status-{data['status']}">
                <td>{metric}</td>
                <td>{data['score']}</td>
                <td>{data['threshold']}</td>
                <td>{data['status']}</td>
            </tr>
            """
        html += "</table>"

    html += "</body></html>"

    (output_dir / "eval_report.html").write_text(html, encoding="utf-8")
    print(f"Generated report in {output_dir}/eval_report.html")

        # Save HTML report
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial; margin: 40px; }
            table { border-collapse: collapse; margin-bottom: 30px; width: 80%; }
            th, td { border: 1px solid #ccc; padding: 8px; }
            th { background-color: #eee; }
            .status-PASSED { background-color: #c8f7c5; }
            .status-FAILED { background-color: #f7c5c5; }
        </style>
    </head>
    <body>
    <h1>ADK Evaluation Report</h1>
    <h2>Overall Status: <span class="status-{status}">{status}</span></h2>
    <h3>Overall Metrics</h3>
    <table>
        <tr><th>Metric</th><th>Score</th><th>Threshold</th><th>Status</th></tr>
    """.format(status=summary["overall_status"])

    for metric, data in summary["overall_metrics"].items():
        html += f"""
        <tr class="status-{data['status']}">
            <td>{metric}</td>
            <td>{data['score']}</td>
            <td>{data['threshold']}</td>
            <td>{data['status']}</td>
        </tr>
        """

    html += "</table><h3>Test Cases</h3>"

    for case in summary["cases"]:
        html += f"""
        <h4>Case: {case['eval_id']} — <span class="status-{case['status']}">{case['status']}</span></h4>
        <table>
            <tr><th>Metric</th><th>Score</th><th>Threshold</th><th>Status</th></tr>
        """
        for metric, data in case["metrics"].items():
            html += f"""
            <tr class="status-{data['status']}">
                <td>{metric}</td>
                <td>{data['score']}</td>
                <td>{data['threshold']}</td>
                <td>{data['status']}</td>
            </tr>
            """
        html += "</table>"

    html += "</body></html>"

    (output_dir / "eval_report.html").write_text(html)

    print("Generated report in eval_reports/")