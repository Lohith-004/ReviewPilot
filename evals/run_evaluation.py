import asyncio
import json
import time
from pathlib import Path

from app.services.llm_reviewer import LLMReviewer


BASE_DIR = Path(__file__).resolve().parent
CASES_FILE = BASE_DIR / "cases" / "review_cases.json"


def load_cases() -> list[dict]:
    with CASES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value) -> str | None:
    if value is None:
        return None

    if hasattr(value, "value"):
        value = value.value

    return str(value).strip().lower()


def evaluate_case(
    case: dict,
    result,
    latency: float,
) -> dict:
    expected = case["expected"]
    findings = result.findings

    min_findings = expected["min_findings"]

    # Detection
    if min_findings == 0:
        detection_pass = len(findings) == 0
    else:
        detection_pass = len(findings) >= min_findings

    # Category
    category_pass = True

    if expected.get("category"):
        expected_category = normalize(expected["category"])

        category_pass = any(
            normalize(finding.category) == expected_category
            for finding in findings
        )

    # Severity
    severity_pass = True

    if expected.get("severity"):
        expected_severity = normalize(expected["severity"])

        severity_pass = any(
            normalize(finding.severity) == expected_severity
            for finding in findings
        )

    passed = (
        detection_pass
        and category_pass
        and severity_pass
    )

    return {
        "id": case["id"],
        "name": case["name"],
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "finding_count": len(findings),
        "expected_min_findings": min_findings,
        "detection_pass": detection_pass,
        "category_pass": category_pass,
        "severity_pass": severity_pass,
        "latency_seconds": round(latency, 2),
    }


async def run_case(
    reviewer: LLMReviewer,
    case: dict,
) -> dict:

    print(f"\nRunning: {case['name']}")
    print("-" * 60)

    start = time.perf_counter()

    try:
        result = await reviewer.review(
            filename=case["filename"],
            patch=case["patch"],
        )

        latency = time.perf_counter() - start

        evaluation = evaluate_case(
            case=case,
            result=result,
            latency=latency,
        )

        print(f"Findings: {len(result.findings)}")
        print(
            f"Expected minimum: "
            f"{case['expected']['min_findings']}"
        )

        # Print actual findings for transparency.
        for index, finding in enumerate(
            result.findings,
            start=1,
        ):
            print(
                f"  Finding {index}: "
                f"{finding.category.value} / "
                f"{finding.severity.value}"
            )

        print(f"Latency: {latency:.2f}s")

        print(
            f"Detection: "
            f"{'PASS' if evaluation['detection_pass'] else 'FAIL'}"
        )

        if case["expected"].get("category"):
            print(
                f"Category: "
                f"{'PASS' if evaluation['category_pass'] else 'FAIL'}"
            )

        if case["expected"].get("severity"):
            print(
                f"Severity: "
                f"{'PASS' if evaluation['severity_pass'] else 'FAIL'}"
            )

        print(
            f"Overall: "
            f"{'PASS' if evaluation['passed'] else 'FAIL'}"
        )

        return evaluation

    except Exception as exc:
        latency = time.perf_counter() - start

        print(
            f"ERROR after {latency:.2f}s: "
            f"{type(exc).__name__}: {exc}"
        )

        return {
            "id": case["id"],
            "name": case["name"],
            "status": "ERROR",
            "passed": False,
            "finding_count": 0,
            "expected_min_findings": case["expected"][
                "min_findings"
            ],
            "detection_pass": False,
            "category_pass": False,
            "severity_pass": False,
            "latency_seconds": round(latency, 2),
        }


def print_summary(results: list[dict]) -> None:

    total = len(results)

    passed = sum(
        result["passed"]
        for result in results
    )

    errors = sum(
        result["status"] == "ERROR"
        for result in results
    )

    detection_passed = sum(
        result["detection_pass"]
        for result in results
    )

    category_results = [
        result
        for result in results
        if result["status"] != "ERROR"
        and result["category_pass"] is not None
    ]

    severity_results = [
        result
        for result in results
        if result["status"] != "ERROR"
        and result["severity_pass"] is not None
    ]

    successful_results = [
        result
        for result in results
        if result["status"] != "ERROR"
    ]

    avg_latency = (
        sum(
            result["latency_seconds"]
            for result in successful_results
        )
        / len(successful_results)
        if successful_results
        else 0
    )

    print("\n")
    print("=" * 60)
    print("REVIEWPILOT EVALUATION SUMMARY")
    print("=" * 60)

    print(f"Cases:              {total}")
    print(f"Passed:             {passed}")
    print(f"Failed:             {total - passed - errors}")
    print(f"Errors:             {errors}")

    if total:
        print(
            f"Overall accuracy:   "
            f"{(passed / total) * 100:.1f}%"
        )

        print(
            f"Detection accuracy: "
            f"{(detection_passed / total) * 100:.1f}%"
        )

    if category_results:
        category_passed = sum(
            result["category_pass"]
            for result in category_results
        )

        print(
            f"Category accuracy:  "
            f"{(category_passed / len(category_results)) * 100:.1f}%"
        )

    if severity_results:
        severity_passed = sum(
            result["severity_pass"]
            for result in severity_results
        )

        print(
            f"Severity accuracy:  "
            f"{(severity_passed / len(severity_results)) * 100:.1f}%"
        )

    print(f"Average latency:    {avg_latency:.2f}s")

    print("=" * 60)

    print("\nCase Results")
    print("-" * 60)

    for result in results:
        print(
            f"{result['status']:<7} "
            f"{result['name']:<30} "
            f"{result['latency_seconds']:>7.2f}s"
        )


async def main() -> None:

    cases = load_cases()

    print("=" * 60)
    print("ReviewPilot Evaluation Harness")
    print("=" * 60)

    print(f"Loaded {len(cases)} benchmark cases.")

    reviewer = LLMReviewer()

    results = []

    for case in cases:
        result = await run_case(
            reviewer=reviewer,
            case=case,
        )

        results.append(result)

    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())