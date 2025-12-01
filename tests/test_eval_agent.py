from pathlib import Path
import json
import traceback
import sys

import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

# Add project root to Python path so 'src' module can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

EVAL_DIR = "./Scripts/evals"
EVAL_RESULT_DIR = "./tests/results"

output_dir = Path(EVAL_RESULT_DIR)
output_dir.mkdir(parents=True, exist_ok=True)

@pytest.mark.asyncio
async def test_with_single_test_file(capfd):
    """Run ADK eval and save the console metrics to a file."""

    # Note: eval_config can be specified in Scripts/evals/test_config.json instead
    # eval_config = EvalConfig(
    #     criteria={
    #         "tool_trajectory_avg_score": BaseCriterion(threshold=0.95),
    #         "response_match_score": BaseCriterion(threshold=0.5),
    #     }
    # )

    path = Path(EVAL_DIR) / "evalset_complete_happypath.evalset.json"

    try:
        # This call raises AssertionError if any metric fails
        await AgentEvaluator.evaluate(
            agent_module="mortgage_deposit_agent",
            eval_dataset_file_path_or_dir=str(path),
            num_runs=1,
            print_detailed_results=True,
        )

    except Exception as e:
        # Capture output even on failure
        out, err = capfd.readouterr()

        error_payload = {
            "error_type": type(e).__name__,
            "error_str": str(e),
            "traceback": traceback.format_exc(),
            "stdout": out,
            "stderr": err,
        }
        (output_dir / "eval_error.json").write_text(
            json.dumps(error_payload, indent=2),
            encoding="utf-8",
        )
        raise

    finally:
        # Capture all printed output (eval results and metrics)
        out, err = capfd.readouterr()

        # Save the console output (this should include the metric table
        # with tool_trajectory_avg_score and response_match_score).
        if out or err:
            (output_dir / "eval_console_output.txt").write_text(
                out + ("\n\n[stderr]\n" + err if err else ""),
                encoding="utf-8",
            )
            print(f"\n✓ Saved evaluation output to {output_dir / 'eval_console_output.txt'}")

            # Also print to console for immediate viewing
            if out:
                print("\n" + "="*80)
                print("EVALUATION RESULTS:")
                print("="*80)
                print(out)
                print("="*80)
