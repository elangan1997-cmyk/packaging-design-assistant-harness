from __future__ import annotations

import json
import base64
import platform
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from packaging_assistant.capabilities import capability_report
from packaging_assistant.exceptions import PackagingAssistantError, RequestValidationError
from packaging_assistant.models import PackagingJob, PackagingRequest, PackagingResult
from packaging_assistant.modules.content import generate_content_layout, write_content_outputs
from packaging_assistant.modules.mockup import generate_mockup, write_mockup_outputs
from packaging_assistant.modules.structure import generate_structure_template, write_structure_outputs
from packaging_assistant.parsers import inspect_asset
from packaging_assistant.routing import route_request
from packaging_assistant.validators import validate_request


def _health_payload() -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[3]
    schema_names = (
        "request.schema.json",
        "job-manifest.schema.json",
        "content-brief.schema.json",
        "content-spec.schema.json",
        "provider-config.schema.json",
        "cmf-plan.schema.json",
        "visual-qa.schema.json",
        "route-decision.schema.json",
    )
    checks: dict[str, bool] = {
        "python_supported": sys.version_info >= (3, 9),
        "package_importable": True,
        "cli_executable": Path(sys.executable).with_name("packaging-assistant").is_file(),
        "schemas_present": all((repository_root / "schemas" / name).is_file() for name in schema_names),
        "examples_present": (repository_root / "examples" / "full-workflow" / "run_demo.py").is_file(),
    }
    try:
        sample = generate_structure_template(
            {
                "model_code": "锁底盒",
                "dimensions": {"length": 40, "width": 20, "height": 60, "unit": "mm"},
            }
        )
        checks["structure_engine"] = sample.svg.startswith("<?xml") and "LAYER_CUT" in sample.svg
    except PackagingAssistantError:
        checks["structure_engine"] = False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "write-probe"
            probe.write_text("ok", encoding="utf-8")
            checks["output_writable"] = probe.read_text(encoding="utf-8") == "ok"
    except OSError:
        checks["output_writable"] = False
    return {
        "healthy": all(checks.values()),
        "python": platform.python_version(),
        "python_supported": checks["python_supported"],
        "web_required": False,
        "node_required": False,
        "checks": checks,
        "capabilities": capability_report(),
    }


def _validate_file(path_value: object) -> dict[str, Any]:
    if not isinstance(path_value, str) or not path_value:
        raise RequestValidationError(
            "MISSING_REQUIRED_FIELD", "缺少待验证文件。", {"missing_fields": ["file"]}
        )
    path = Path(path_value).expanduser()
    if not path.is_file():
        raise RequestValidationError("INPUT_NOT_FOUND", f"文件不存在：{path}", {"path": str(path)})
    issues: list[dict[str, str]] = []
    if path.suffix.lower() == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append({"code": "INVALID_JSON", "message": str(exc), "severity": "error"})
    elif path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<svg" not in text:
            issues.append({"code": "INVALID_SVG", "message": "缺少 svg 根元素。", "severity": "error"})
    return {"valid": not issues, "issues": issues, "asset": asdict(inspect_asset(path))}


def run_request(
    request_data: dict[str, Any] | PackagingRequest,
    output_dir: str | Path | None = None,
    *,
    dry_run: bool = False,
) -> PackagingResult:
    request = request_data if isinstance(request_data, PackagingRequest) else PackagingRequest.from_dict(request_data)
    try:
        validate_request(request)
        route = route_request(request)
        route_payload = asdict(route)
        if dry_run:
            return PackagingResult(
                success=True,
                action=request.action,
                request_id=request.request_id,
                status="dry_run",
                outputs=[],
                warnings=[],
                manual_review_required=bool(route.manual_review_items),
                route=route_payload,
            )
        if route.missing_fields and request.action != "route":
            return PackagingResult(
                success=False,
                action=request.action,
                request_id=request.request_id,
                status="needs_input",
                outputs=[],
                warnings=[],
                manual_review_required=bool(route.manual_review_items),
                error={
                    "code": "MISSING_REQUIRED_FIELD",
                    "message": "缺少执行该操作所需的字段。",
                    "details": {
                        "missing_fields": route.missing_fields,
                        "choice_prompt": route.choice_prompt,
                    },
                },
                route=route_payload,
            )

        if request.action == "structure_template" and route.implemented:
            generation = generate_structure_template(request.parameters)
            warnings = list(generation.validation["warnings"])
            if output_dir is None:
                outputs = [
                    {"type": "svg", "name": "template.svg", "inline": generation.svg},
                    {"type": "json", "name": "structure_spec.json", "inline": generation.spec},
                    {"type": "json", "name": "validation_report.json", "inline": generation.validation},
                ]
                job_id = ""
            else:
                from packaging_assistant.orchestrator.workspace import JobWorkspace

                job = PackagingJob(
                    workflow=request.action,
                    request_id=request.request_id,
                    status="completed",
                    structure=generation.spec,
                    warnings=warnings,
                    manual_review_required=True,
                )
                workspace = JobWorkspace(output_dir, job).create()
                paths = write_structure_outputs(generation, workspace.path)
                outputs = [
                    {"type": "svg" if path.suffix == ".svg" else "json", "path": str(path)}
                    for path in paths
                ]
                job.outputs.extend(outputs)
                workspace.write_manifest()
                job_id = job.job_id
            return PackagingResult(
                success=True,
                action=request.action,
                request_id=request.request_id,
                status="completed",
                job_id=job_id,
                outputs=outputs,
                warnings=warnings,
                manual_review_required=True,
                route=route_payload,
            )

        if request.action == "content_layout" and route.implemented:
            generation = generate_content_layout(request.parameters)
            warnings = list(generation.validation["warnings"])
            if output_dir is None:
                outputs = [
                    {"type": "svg", "name": "content-layout.svg", "inline": generation.svg},
                    {"type": "json", "name": "content-spec.json", "inline": asdict(generation.spec)},
                    {"type": "markdown", "name": "source-report.md", "inline": generation.source_report},
                    {"type": "markdown", "name": "missing-fields.md", "inline": generation.missing_fields_report},
                    {"type": "markdown", "name": "review-checklist.md", "inline": generation.review_checklist},
                ]
                job_id = ""
            else:
                from packaging_assistant.orchestrator.workspace import JobWorkspace

                job = PackagingJob(
                    workflow=request.action,
                    request_id=request.request_id,
                    status="completed",
                    jurisdiction=generation.spec.jurisdiction,
                    product_category=generation.spec.product_category,
                    content=asdict(generation.spec),
                    warnings=warnings,
                    manual_review_required=True,
                )
                workspace = JobWorkspace(output_dir, job).create()
                paths = write_content_outputs(generation, workspace.path)
                outputs = [
                    {
                        "type": "svg" if path.suffix == ".svg" else "json" if path.suffix == ".json" else "markdown",
                        "path": str(path),
                    }
                    for path in paths
                ]
                job.outputs.extend(outputs)
                workspace.write_manifest()
                job_id = job.job_id
            return PackagingResult(
                success=True,
                action=request.action,
                request_id=request.request_id,
                status="completed",
                job_id=job_id,
                outputs=outputs,
                warnings=warnings,
                manual_review_required=True,
                route=route_payload,
            )

        if request.action == "mockup_render" and route.implemented:
            generation = generate_mockup(request.parameters)
            warnings = list(generation.warnings)
            if output_dir is None:
                outputs = [
                    {
                        "type": "image",
                        "name": "mockup.png",
                        "mime_type": generation.mime_type,
                        "inline_base64": base64.b64encode(generation.image_bytes).decode("ascii"),
                    },
                    {"type": "json", "name": "cmf-plan.json", "inline": generation.cmf_plan},
                    {
                        "type": "json",
                        "name": "generation-record.json",
                        "inline": generation.generation_record,
                    },
                    {
                        "type": "json",
                        "name": "visual-qa.json",
                        "inline": asdict(generation.visual_qa),
                    },
                    {
                        "type": "json",
                        "name": "retry-record.json",
                        "inline": generation.retry_record,
                    },
                    {
                        "type": "markdown",
                        "name": "review-checklist.md",
                        "inline": generation.review_checklist,
                    },
                ]
                job_id = ""
            else:
                from packaging_assistant.orchestrator.workspace import JobWorkspace

                job = PackagingJob(
                    workflow=request.action,
                    request_id=request.request_id,
                    status=generation.status,
                    assets=route.input_assets,
                    finishes=list(generation.cmf_plan.get("finishes", [])),
                    providers={
                        "generation": generation.generation_record.get("provider", ""),
                        "visual_qa": generation.visual_qa.provider,
                        "mock": generation.generation_record.get("mock", False),
                    },
                    warnings=warnings,
                    manual_review_required=generation.status != "completed",
                )
                workspace = JobWorkspace(output_dir, job).create()
                paths = write_mockup_outputs(generation, workspace.path)
                outputs = [
                    {
                        "type": "image" if path.suffix == ".png" else "json" if path.suffix == ".json" else "markdown",
                        "path": str(path),
                    }
                    for path in paths
                ]
                job.outputs.extend(outputs)
                workspace.write_manifest()
                job_id = job.job_id
            return PackagingResult(
                success=True,
                action=request.action,
                request_id=request.request_id,
                status=generation.status,
                job_id=job_id,
                outputs=outputs,
                warnings=warnings,
                manual_review_required=generation.status != "completed",
                route=route_payload,
            )

        payload: dict[str, Any]
        filename: str
        if request.action == "health_check":
            payload, filename = _health_payload(), "health_report.json"
        elif request.action == "inspect":
            input_value = request.parameters.get("input") or request.parameters.get("file")
            if not isinstance(input_value, str) or not input_value:
                raise RequestValidationError(
                    "MISSING_REQUIRED_FIELD", "缺少待检查输入。", {"missing_fields": ["input"]}
                )
            payload, filename = asdict(inspect_asset(input_value)), "inspection.json"
        elif request.action == "route":
            payload, filename = route_payload, "route.json"
        elif request.action == "validate":
            payload, filename = _validate_file(request.parameters.get("file")), "validation.json"
        elif not route.implemented:
            return PackagingResult(
                success=False,
                action=request.action,
                request_id=request.request_id,
                status="not_implemented",
                warnings=[],
                manual_review_required=True,
                error={
                    "code": "NOT_IMPLEMENTED",
                    "message": route.reason,
                    "module": route.module,
                },
                route=route_payload,
            )
        else:
            raise PackagingAssistantError("INTERNAL_ROUTING_ERROR", "已实现 action 缺少执行器。")

        outputs: list[dict[str, Any]] = []
        job_id = ""
        if output_dir is not None:
            job = PackagingJob(workflow=request.action, request_id=request.request_id, status="completed")
            from packaging_assistant.orchestrator.workspace import JobWorkspace

            workspace = JobWorkspace(output_dir, job).create()
            result_path = workspace.write_json(filename, payload)
            job.outputs.append({"type": "json", "path": str(result_path)})
            job.updated_at = job.created_at
            workspace.write_manifest()
            job_id = job.job_id
            outputs.append({"type": "json", "path": str(result_path)})
        else:
            outputs.append({"type": "json", "inline": payload})
        return PackagingResult(
            success=True,
            action=request.action,
            request_id=request.request_id,
            status="completed",
            job_id=job_id,
            outputs=outputs,
            warnings=[],
            manual_review_required=bool(route.manual_review_items),
            route=route_payload,
        )
    except PackagingAssistantError as exc:
        return PackagingResult(
            success=False,
            action=request.action,
            request_id=request.request_id,
            status="failed",
            error=exc.to_dict(),
            manual_review_required=True,
        )
