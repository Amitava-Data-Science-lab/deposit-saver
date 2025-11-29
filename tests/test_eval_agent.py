from google.adk.evaluation.agent_evaluator import AgentEvaluator, EvalConfig
import pytest, json

EVAL_DIR = "./Scripts/evals"
EVAL_RESULT_DIR = "./tests/results"

@pytest.mark.asyncio
async def test_with_single_test_file():
    """Test the agent's basic ability via a session file."""
    eval_config = EvalConfig()

    result = await AgentEvaluator.evaluate(
        agent_module="mortgage_deposit_agent",
        eval_dataset_file_path_or_dir=f"{EVAL_DIR}/evalset_postcode_error.evalset.json",
        eval_config=eval_config,
        num_runs=3,  # optional
        print_detailed_results=True,
    )

    # Save detailed results to a JSON file
    with open(f"{EVAL_RESULT_DIR}/eval_output.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    # ---- Extract metric summary ----
    summary = {
        "overall_status": result.overall_status.name,
        "overall_metrics": {},
        "cases": []
    }

    for metric in result.metric_results:
        summary["overall_metrics"][metric.metric_name] = {
            "score": metric.score,
            "threshold": metric.threshold,
            "status": metric.eval_status.name,
        }

    # Per-eval-case details
    for case in result.eval_case_results:
        case_entry = {
            "eval_id": case.eval_id,
            "status": case.overall_status.name,
            "metrics": {},
        }
        for m in case.metric_results:
            case_entry["metrics"][m.metric_name] = {
                "score": m.score,
                "threshold": m.threshold,
                "status": m.eval_status.name,
            }
        summary["cases"].append(case_entry)

    # Save summary
    with open(f"{EVAL_RESULT_DIR}/eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    await save_as_html(EVAL_RESULT_DIR, summary)


    # Keep the assertion behaviour
    assert result.overall_status.is_pass, "Eval failed – see eval_output.json"

async def save_as_html(OUTPUT_DIR, summary):
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

    (OUTPUT_DIR / "eval_report.html").write_text(html)

    print("Generated report in eval_reports/")