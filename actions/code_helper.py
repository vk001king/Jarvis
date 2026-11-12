import subprocess
import sys
import json
import re
import time
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR           = get_base_dir()
API_CONFIG_PATH    = BASE_DIR / "config" / "api_keys.json"
DESKTOP            = Path.home() / "Desktop"
MAX_BUILD_ATTEMPTS = 3
# Model choice lives in core/gemini.py, and so does the timeout and the
# fallback ladder. Writing a model name here is what left this file hanging
# forever whenever that one alias was unwell.
from core import gemini


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _get_gemini(tier: str = gemini.SMART):
    """Writing and fixing code is the reasoning tier; a 60s deadline because a
    whole file can come back."""
    class _W:
        def generate_content(self, contents):
            resp = gemini.call(contents, tier=tier, timeout_ms=60000)
            if resp is None:
                raise RuntimeError("every Gemini model on the ladder failed")
            return resp

    return _W()


def _clean_code(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _resolve_save_path(output_path: str, language: str) -> Path:
    ext_map = {
        "python": ".py", "py": ".py",
        "javascript": ".js", "js": ".js",
        "typescript": ".ts", "ts": ".ts",
        "html": ".html", "css": ".css",
        "java": ".java", "cpp": ".cpp", "c": ".c",
        "bash": ".sh", "shell": ".sh", "powershell": ".ps1",
        "sql": ".sql", "json": ".json", "rust": ".rs", "go": ".go",
    }
    if output_path:
        p = Path(output_path)
        return p if p.is_absolute() else DESKTOP / p
    ext = ext_map.get((language or "python").lower(), ".py")
    return DESKTOP / f"jarvis_code{ext}"


def _read_file(file_path: str) -> tuple[str, str]:
    if not file_path:
        return "", "No file path provided."
    p = Path(file_path)
    if not p.exists():
        return "", f"File not found: {file_path}"
    try:
        return p.read_text(encoding="utf-8"), ""
    except Exception as e:
        return "", f"Could not read file: {e}"


def _save_file(path: Path, content: str) -> str:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Saved to: {path}"
    except Exception as e:
        return f"Could not save: {e}"


def _preview(code: str, lines: int = 10) -> str:
    all_lines = code.splitlines()
    preview   = "\n".join(all_lines[:lines])
    suffix    = f"\n... ({len(all_lines) - lines} more lines)" if len(all_lines) > lines else ""
    return preview + suffix


def _has_error(output: str) -> bool:
    error_signals = ["error", "exception", "traceback", "syntaxerror",
                     "nameerror", "typeerror", "stderr", "failed", "crash"]
    return any(s in output.lower() for s in error_signals)


def _take_screenshot() -> Path | None:
    try:
        import pyautogui
        screenshot_path = Path.home() / "Desktop" / f"jarvis_debug_{int(time.time())}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(str(screenshot_path))
        print(f"[Code] 📸 Screenshot: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"[Code] ⚠️ Screenshot failed: {e}")
        return None


def _image_to_base64(path: Path) -> str:
    import base64
    return base64.b64encode(path.read_bytes()).decode("utf-8")


_VALID_INTENTS = {
    "write", "edit", "explain", "run", "build", "screen_debug", "optimize",
    "refactor", "document", "test", "review", "debug", "generate", "convert",
    "scan", "audit", "lint", "format", "migrate", "prototype", "computer_use",
    "browser", "automation", "operator", "vision", "click", "type", "scroll",
    "navigate", "browse", "screenshot"
}

# 100+ feature shortcuts: each key maps to a common workflow the agent can perform.
# We keep them in a registry so the tool supports many real-world development tasks
# without adding a pile of one-off code paths.
_EXTRA_FEATURES = {
    "generate_api": "Generate an API implementation",
    "generate_backend": "Generate backend logic and service layers",
    "generate_frontend": "Generate frontend UI and component code",
    "generate_fullstack": "Generate a full-stack app structure",
    "generate_cli": "Generate a command-line interface",
    "generate_dashboard": "Generate a dashboard screen with data widgets",
    "generate_website": "Generate a website landing page or app shell",
    "generate_webapp": "Generate a web application scaffold",
    "generate_mobile_app": "Generate a mobile app starter",
    "generate_desktop_app": "Generate a desktop application scaffold",
    "generate_game": "Generate a simple game prototype",
    "generate_script": "Generate a standalone automation script",
    "generate_automation": "Generate automation workflow code",
    "generate_scraper": "Generate a scraper or crawler script",
    "generate_bot": "Generate a bot or automation agent",
    "generate_chatbot": "Generate a conversational chatbot",
    "generate_ml_model": "Generate a machine learning model template",
    "generate_data_pipeline": "Generate a data pipeline or ETL flow",
    "generate_etl": "Generate ETL processing code",
    "generate_sql_query": "Generate SQL query logic",
    "generate_regex": "Generate regular expressions",
    "generate_rest_api": "Generate a REST API service",
    "generate_graphql_api": "Generate a GraphQL API service",
    "generate_microservice": "Generate a microservice module",
    "generate_crud": "Generate CRUD operations",
    "generate_auth_system": "Generate authentication and authorization code",
    "generate_payment_integration": "Generate payment integration logic",
    "generate_email_service": "Generate an email sending service",
    "generate_notification_service": "Generate event and notification handling",
    "generate_analytics_module": "Generate analytics and metrics code",
    "generate_reporting_module": "Generate reporting and export logic",
    "generate_security_audit": "Generate a security audit checklist and hardened code",
    "generate_monitoring": "Generate monitoring and observability hooks",
    "generate_logging": "Generate structured logging code",
    "generate_cache_layer": "Generate a cache integration layer",
    "generate_caching": "Generate caching patterns and code",
    "generate_cache": "Generate cache-related logic",
    "generate_dockerfile": "Generate a Dockerfile",
    "generate_kubernetes_manifest": "Generate a Kubernetes deployment manifest",
    "generate_ci_pipeline": "Generate a CI pipeline configuration",
    "generate_cd_pipeline": "Generate a CD deployment pipeline",
    "generate_makefile": "Generate a Makefile or build helper",
    "generate_requirements": "Generate dependency and requirements configuration",
    "generate_package_json": "Generate a package.json configuration",
    "generate_pyproject": "Generate a pyproject.toml configuration",
    "generate_vscode_settings": "Generate VS Code workspace settings",
    "generate_readme": "Generate project README documentation",
    "generate_docs": "Generate technical documentation",
    "generate_api_docs": "Generate API reference documentation",
    "generate_architecture": "Generate an architecture plan or diagram scaffolding",
    "refactor_code": "Refactor the code for clarity and maintainability",
    "refactor_module": "Refactor a module into cleaner components",
    "clean_code": "Clean up code quality and formatting issues",
    "simplify_logic": "Simplify the logic flow and complexity",
    "optimize_query": "Optimize database or query logic",
    "optimize_database": "Optimize data access and storage design",
    "optimize_performance": "Optimize runtime and resource usage",
    "decompose_component": "Decompose a component into smaller units",
    "reduce_complexity": "Reduce complexity in the implementation",
    "remove_dead_code": "Remove unused or dead code",
    "improve_types": "Improve typing and static type safety",
    "improve_readability": "Improve readability and maintainability",
    "fix_bug": "Diagnose and fix the underlying bug",
    "debug_code": "Debug the implementation and isolate the issue",
    "trace_error": "Trace the failing error path and root cause",
    "diagnose_issue": "Diagnose the reported issue thoroughly",
    "explain_architecture": "Explain the code architecture and structure",
    "review_security": "Review security posture and risks",
    "review_code": "Review the code for quality and correctness",
    "review_pr": "Review the patch and highlight issues",
    "test_code": "Test the implementation and validate behavior",
    "generate_tests": "Generate focused automated tests",
    "create_unit_tests": "Create unit tests for the module",
    "create_integration_tests": "Create integration tests for the flow",
    "create_e2e_tests": "Create end-to-end tests for the feature",
    "add_coverage": "Add coverage and validation cases",
    "mock_dependencies": "Mock dependencies and isolate behavior",
    "fix_tests": "Fix failing tests and validation issues",
    "run_tests": "Run the relevant test suite",
    "validate_build": "Validate project build and runtime health",
    "lint_code": "Lint and check the code for quality issues",
    "format_code": "Format the codebase consistently",
    "convert_code": "Convert code to another language or target framework",
    "migrate_code": "Migrate the implementation to a newer platform",
    "port_app": "Port or adapt the app to another runtime",
    "modernize_code": "Modernize the implementation and dependencies",
    "upgrade_dependencies": "Upgrade the dependency set safely",
    "scan_vulnerabilities": "Scan the codebase for vulnerabilities",
    "analyze_performance": "Analyze performance bottlenecks",
    "inspect_runtime": "Inspect the runtime path and execution issues",
    "inspect_memory": "Inspect memory usage and leaks",
    "inspect_logs": "Inspect logs and error reports",
    "transform_data": "Transform data from one format to another",
    "parse_data": "Parse and normalize input data",
    "summarize_logs": "Summarize logs for actionable insights",
    "infer_schema": "Infer schema and data structure from samples",
    "diagram_flow": "Diagram the request or execution flow",
    "create_ui_mock": "Create a UI mock or prototype sketch",
    "create_wireframe": "Create a wireframe layout",
    "create_prototype": "Create a rapid prototype implementation",
    "document_api": "Document the API contract",
    "document_module": "Document the internal module structure",
    "document_feature": "Document a feature end-to-end",
    "document_service": "Document the service architecture",
    "document_process": "Document a business or technical process",
    "generate_changelog": "Generate a changelog summary",
    "generate_release_notes": "Generate release notes",
    "generate_config": "Generate configuration for deployment or runtime",
    "generate_env_example": "Generate environment variable examples",
    "generate_error_handler": "Generate resilient error handling",
    "generate_backup_plan": "Generate a backup and restore plan",
    "generate_monitoring_alerts": "Generate monitoring alert rules",
    "generate_observability": "Generate observability instrumentation",
    "generate_schema": "Generate an input or output schema",
    "generate_contract": "Generate an interface or contract definition",
    "generate_data_model": "Generate a data model definition",
    "generate_benchmark": "Generate benchmark and performance harness code",
    "generate_cli_tool": "Generate a reusable CLI helper tool",
    "generate_component": "Generate a reusable UI or service component",
    "generate_plugin": "Generate a plugin or extension scaffold",
    "generate_adapter": "Generate adapter or translation logic",
    "generate_wrapper": "Generate a wrapper abstraction around a library",
    "generate_migration": "Generate a migration script",
    "generate_seed_data": "Generate seed data for development or testing",
    "generate_templates": "Generate reusable templates for common patterns",
    "generate_validation": "Generate validation and sanitization logic",
    "generate_schemas": "Generate schemas for structured data",
    "generate_forms": "Generate form handling and validation",
    "generate_tables": "Generate table definitions for persistence",
    "generate_query_builder": "Generate a query builder abstraction",
    "generate_config_loader": "Generate configuration loader code",
    "generate_cache_strategy": "Generate a cache strategy and invalidation plan",
    "generate_job_queue": "Generate a job queue or worker pipeline",
    "generate_event_bus": "Generate event bus and pub-sub logic",
    "generate_state_machine": "Generate a state machine implementation",
    "generate_workflow": "Generate a workflow orchestration script",
    "generate_realtime_feature": "Generate a realtime feature or event stream",
    "generate_search_index": "Generate search indexing logic",
    "generate_filtering": "Generate filtering and query logic",
    "generate_sorting": "Generate sorting and ranking logic",
    "generate_pagination": "Generate pagination logic",
    "generate_access_control": "Generate access-control and permission logic",
    "generate_error_reporting": "Generate error-reporting and telemetry logic",
    "generate_localization": "Generate locale-aware text and localization helpers",
    "generate_import_export": "Generate import/export utilities",
    "generate_reconciliation": "Generate reconciliation or sync logic",
    "generate_cache_warmer": "Generate a cache warming strategy",
    "generate_metrics": "Generate metrics and monitoring instrumentation",
    "generate_audit_log": "Generate audit logging for actions and events",
    "generate_feature_flag": "Generate feature flag toggles and evaluation code",
    "generate_task_runner": "Generate a task runner or scheduler",
    "generate_worker_pool": "Generate a worker pool or concurrent task manager",
    "generate_retry_logic": "Generate retry and backoff logic",
    "generate_retry": "Generate retry and resilience code",
    "generate_healthcheck": "Generate health check endpoints or logic",
    "computer_use": "Use the computer like a browser and desktop automation agent",
    "use_computer": "Use the computer like a browser and desktop automation agent",
    "desktop_agent": "Use the desktop as an autonomous computer-use agent",
    "browser_agent": "Use the browser and desktop like an autonomous operator",
    "open_browser": "Open and control a browser session for the task",
    "browse_web": "Browse the web and complete the user task using browser actions",
    "search_web": "Search the web and inspect the results",
    "navigate_site": "Navigate a website and interact with it",
    "click_element": "Click UI elements on screen or in the browser",
    "type_text": "Type text into an app or browser field",
    "scroll_page": "Scroll the active page or window",
    "take_screenshot": "Capture a screenshot and inspect it",
    "inspect_screen": "Inspect the screen and explain what is visible",
    "summarize_screen": "Summarize the visible screen and identify actions",
    "open_app": "Open an application and interact with it",
    "switch_app": "Switch between apps or windows",
    "move_mouse": "Move the mouse and click or drag on screen",
    "drag_drop": "Drag and drop elements on the screen",
    "hotkey": "Trigger keyboard shortcuts and system commands",
    "copy_text": "Copy text from the active UI",
    "paste_text": "Paste clipboard text into the current field",
    "fill_form": "Fill a form using the computer and browser",
    "submit_form": "Submit a form or action on the active page",
    "login_website": "Log in to a website using browser automation",
    "extract_data": "Extract data from a UI, page, or file",
    "read_document": "Read and summarize a document or page",
    "organize_files": "Organize files and folders on the system",
    "manage_files": "Manage files, folders, and documents",
    "inspect_files": "Inspect files and summarize the contents",
    "save_to_file": "Save output to a file on disk",
    "download_file": "Download or save a file from the browser",
    "watch_screen": "Monitor the screen and react to visible changes",
    "operate_browser": "Operate the browser as an autonomous web agent",
    "control_pc": "Control the PC and complete the requested task",
    "computer_operator": "Act as a computer operator for the requested task",
    "assistant_operator": "Act as an autonomous assistant using the computer",
}

_FEATURE_ALIASES = {
    "generate": "generate_api",
    "create": "generate_api",
    "make": "generate_api",
    "analyze": "review_code",
    "audit": "review_security",
    "scan": "scan_vulnerabilities",
    "probe": "diagnose_issue",
    "document": "generate_readme",
    "docs": "generate_docs",
    "refactor": "refactor_code",
    "clean": "clean_code",
    "debug": "debug_code",
    "troubleshoot": "diagnose_issue",
    "test": "test_code",
    "qa": "test_code",
    "lint": "lint_code",
    "format": "format_code",
    "migrate": "migrate_code",
    "prototype": "create_prototype",
    "convert": "convert_code",
    "operator": "computer_use",
    "computer": "computer_use",
    "desktop": "computer_use",
    "browser": "browse_web",
    "screen": "inspect_screen",
    "vision": "inspect_screen",
    "autopilot": "computer_use",
    "click": "click_element",
    "type": "type_text",
    "scroll": "scroll_page",
    "search": "search_web",
    "screenshot": "take_screenshot",
    "app": "open_app",
    "files": "manage_files",
    "download": "download_file",
}


def _normalize_action(action: str) -> str:
    if not action:
        return ""
    normalized = action.strip().lower().replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return _FEATURE_ALIASES.get(normalized, normalized)


def _detect_intent(description: str, file_path: str, code: str) -> str:
    """
    Language-independent intent detection — NO fixed keyword list.
    Whatever language the user speaks, the description is classified by
    Gemini. If the API is unreachable, it falls back to language-agnostic
    structural hints (does the file exist on disk, was code provided).
    """
    desc        = (description or "").strip()
    file_exists = bool(file_path) and Path(file_path).exists()

    if desc:
        try:
            ctx = []
            if file_path:
                ctx.append(f"a file path is provided (exists on disk: {file_exists})")
            if code:
                ctx.append("an inline code snippet is provided")
            prompt = (
                "Classify a coding assistant request into exactly ONE intent word.\n"
                "The request may be written in ANY language.\n\n"
                f"Request: {desc}\n"
                + (f"Context: {'; '.join(ctx)}\n" if ctx else "")
                + "\nIntents:\n"
                "  write        = create new code from scratch\n"
                "  edit         = modify an existing file\n"
                "  explain      = describe what given code/file does\n"
                "  run          = execute an existing file\n"
                "  build        = write code, run it, and iterate until it works\n"
                "  screen_debug = analyze an error currently visible on the user's screen\n"
                "  optimize     = refactor / clean up / speed up existing code\n\n"
                "Reply with ONLY the intent word, nothing else."
            )
            ans = _get_gemini().generate_content(prompt).text.strip().lower()
            ans = ans.strip("`'\". \n")
            if ans in _VALID_INTENTS:
                return ans
        except Exception as e:
            print(f"[Code] Intent classification failed ({e}) — structural fallback")

    # Structural fallback — not tied to any language
    if file_exists:
        return "edit" if desc else "explain"
    if code:
        return "explain"
    return "write"

def _write(description: str, language: str, output_path: str, player=None) -> tuple[str, Path]:
    lang  = language or "python"
    model = _get_gemini()

    prompt = f"""You are an expert {lang} developer.
Write clean, working, well-commented {lang} code for the description below.

Rules:
- Output ONLY the code. No explanation, no markdown, no backticks.
- Add helpful inline comments.
- Handle errors and edge cases properly.
- Use modern best practices.

Description: {description}

Code:"""

    response = model.generate_content(prompt)
    code     = _clean_code(response.text)
    path     = _resolve_save_path(output_path, lang)
    _save_file(path, code)
    return code, path


def _fix_code(code: str, error_output: str, description: str) -> str:
    model  = _get_gemini()
    prompt = f"""You are an expert debugger.
The code below failed with the following error. Fix it.
Return ONLY the corrected code — no explanation, no markdown, no backticks.

Original goal: {description}

Error:
{error_output[:2000]}

Broken code:
{code}

Fixed code:"""

    response = model.generate_content(prompt)
    return _clean_code(response.text)


def _run_file(path: Path, args: list, timeout: int) -> str:
    interpreters = {
        ".py":  [sys.executable],
        ".js":  ["node"],
        ".ts":  ["ts-node"],
        ".sh":  ["bash"],
        ".ps1": ["powershell", "-File"],
        ".rb":  ["ruby"],
        ".php": ["php"],
    }
    interp = interpreters.get(path.suffix.lower())
    if not interp:
        return f"No interpreter for {path.suffix}."

    try:
        result = subprocess.run(
            interp + [str(path)] + (args or []),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout, cwd=str(path.parent)
        )
        output = result.stdout.strip()
        error  = result.stderr.strip()
        parts  = []
        if output: parts.append(f"Output:\n{output}")
        if error:  parts.append(f"Stderr:\n{error}")
        return "\n\n".join(parts) if parts else "Executed with no output."

    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout}s."
    except FileNotFoundError:
        return f"Interpreter not found: {interp[0]}."
    except Exception as e:
        return f"Execution error: {e}"


def _build(description, language, output_path, args, timeout, speak=None, player=None) -> str:
    if not description:
        return "Please describe what you want me to build, sir."

    if player:
        player.write_log("[Code] Build started...")

    lang = language or "python"

    try:
        code, path = _write(description, lang, output_path, player)
        print(f"[Code] ✅ Written: {path}")
    except Exception as e:
        msg = f"Could not write initial code: {e}"
        if speak: speak(msg)
        return msg

    last_output = ""
    for attempt in range(1, MAX_BUILD_ATTEMPTS + 1):
        print(f"[Code] 🔄 Attempt {attempt}/{MAX_BUILD_ATTEMPTS}")
        if player:
            player.write_log(f"[Code] Attempt {attempt}...")

        last_output = _run_file(path, args, timeout)

        if not _has_error(last_output):
            msg = (
                f"Build complete, sir. "
                f"The code is working after {attempt} attempt{'s' if attempt > 1 else ''}. "
                f"Saved to {path}."
            )
            if speak: speak(msg)
            return f"{msg}\n\nOutput:\n{last_output}"

        print(f"[Code] ⚠️ Error on attempt {attempt}, fixing...")
        if player:
            player.write_log(f"[Code] Fixing (attempt {attempt})...")

        try:
            code = _fix_code(code, last_output, description)
            _save_file(path, code)
        except Exception as e:
            msg = f"Could not fix code on attempt {attempt}: {e}"
            if speak: speak(msg)
            return msg

    msg = (
        f"I was unable to build a working version after {MAX_BUILD_ATTEMPTS} attempts, sir. "
        f"The last error was: {last_output[:200]}"
    )
    if speak: speak(msg)
    return f"{msg}\n\nLast code saved to: {path}"

def _write_action(description, language, output_path, player) -> str:
    if not description:
        return "Please describe what you want me to write, sir."
    if player:
        player.write_log("[Code] Writing code...")
    try:
        code, path = _write(description, language, output_path, player)
        print(f"[Code] ✅ Written: {path}")
        return f"Code written. Saved to: {path}\n\nPreview:\n{_preview(code)}"
    except Exception as e:
        return f"Could not generate code: {e}"


def _edit_action(file_path, instruction, player) -> str:
    if not file_path:
        return "Please provide a file path to edit, sir."
    if not instruction:
        return "Please describe what change to make, sir."

    content, err = _read_file(file_path)
    if err:
        return err

    if player:
        player.write_log("[Code] Editing file...")

    model  = _get_gemini()
    prompt = f"""You are an expert code editor.
Apply the following change to the code below.
Return ONLY the complete updated code — no explanation, no markdown, no backticks.

Change: {instruction}

Original code:
{content}

Updated code:"""

    try:
        response = model.generate_content(prompt)
        edited   = _clean_code(response.text)
    except Exception as e:
        return f"Could not edit code: {e}"

    status = _save_file(Path(file_path), edited)
    print(f"[Code] ✅ Edited: {file_path}")
    return f"File edited. {status}\n\nPreview:\n{_preview(edited)}"


def _explain_action(file_path, code, player) -> str:
    if file_path and not code:
        code, err = _read_file(file_path)
        if err:
            return err
    if not code:
        return "Please provide code or a file path to explain, sir."

    if player:
        player.write_log("[Code] Analyzing code...")

    model  = _get_gemini()
    prompt = f"""Explain what this code does in simple, clear language.
Focus on: what it does, how it works, and any important details.
Be concise — 3 to 6 sentences maximum.

Code:
{code[:4000]}

Explanation:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Could not explain code: {e}"


def _run_action(file_path, args, timeout, player) -> str:
    if not file_path:
        return "Please provide a file path to run, sir."
    p = Path(file_path)
    if not p.exists():
        return f"File not found: {file_path}"
    if player:
        player.write_log(f"[Code] Running {p.name}...")
    return _run_file(p, args, timeout)


def _optimize_action(file_path, code, language, output_path, player) -> str:

    if file_path and not code:
        code, err = _read_file(file_path)
        if err:
            return err
    if not code:
        return "Please provide code or a file path to optimize, sir."

    if player:
        player.write_log("[Code] Optimizing code...")

    lang  = language or "python"
    model = _get_gemini()

    prompt = f"""You are an expert {lang} developer and code reviewer.
Optimize the following code for:
1. Performance — eliminate unnecessary operations, use efficient data structures
2. Readability — clear variable names, proper formatting, logical structure
3. Best practices — modern {lang} patterns, error handling, type hints if applicable
4. Remove dead code, redundant comments, and unnecessary complexity

Return ONLY the optimized code — no explanation, no markdown, no backticks.

Original code:
{code[:6000]}

Optimized code:"""

    try:
        response  = model.generate_content(prompt)
        optimized = _clean_code(response.text)
    except Exception as e:
        return f"Could not optimize code: {e}"

    # Kaydet
    if file_path:
        save_path = Path(file_path)
    else:
        save_path = _resolve_save_path(output_path, lang)

    status = _save_file(save_path, optimized)
    print(f"[Code] ✅ Optimized: {save_path}")

    original_lines  = len(code.splitlines())
    optimized_lines = len(optimized.splitlines())
    diff = original_lines - optimized_lines

    return (
        f"Code optimized. {status}\n"
        f"Lines: {original_lines} → {optimized_lines} "
        f"({'−' if diff > 0 else '+'}{abs(diff)} lines)\n\n"
        f"Preview:\n{_preview(optimized)}"
    )


def _screen_debug_action(description, file_path, player, speak=None) -> str:

    if player:
        player.write_log("[Code] Taking screenshot for analysis...")

    print("[Code] 📸 Capturing screen for debug...")


    screenshot_path = _take_screenshot()
    if not screenshot_path:
        return "Could not take screenshot, sir. Please make sure PyAutoGUI is installed."


    file_content = ""
    if file_path:
        file_content, err = _read_file(file_path)
        if err:
            print(f"[Code] ⚠️ Could not read file: {err}")

    try:
        from google.genai import types

        image_bytes  = screenshot_path.read_bytes()
        image_base64 = _image_to_base64(screenshot_path)

        user_question = description or "What error or problem do you see on the screen? How can it be fixed?"

        context = ""
        if file_content:
            context = f"\n\nAdditionally, here is the related file content:\n```\n{file_content[:4000]}\n```"

        analysis_prompt = f"""You are an expert programmer and debugger analyzing a screenshot.

User's question: {user_question}{context}

Please:
1. Identify any errors, exceptions, or problems visible on the screen
2. Explain what is causing the problem in simple terms
3. Provide a concrete fix or solution
4. If there's code visible, show the corrected version

Be specific and actionable. If you see an error message, quote it exactly."""

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            analysis_prompt,
        ]

        response = gemini.call(contents, tier=gemini.SMART, timeout_ms=45_000)
        if response is None:
            return "Sir, I couldn't reach Gemini to analyse that screenshot."

        analysis = (response.text or "").strip()
        print(f"[Code] ✅ Screen analysis complete")

        try:
            screenshot_path.unlink()
        except Exception:
            pass

        if file_path and file_content:

            code_match = re.search(r"```[a-zA-Z]*\n(.*?)```", analysis, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1).strip()
                save_path  = Path(file_path)
                _save_file(save_path, fixed_code)
                analysis += f"\n\n✅ Fixed code has been saved to: {file_path}"
                print(f"[Code] ✅ Fixed code saved: {file_path}")

        return analysis

    except Exception as e:

        try:
            screenshot_path.unlink()
        except Exception:
            pass
        return f"Screen analysis failed: {e}"


_COMPUTER_USE_FEATURES = {
    "computer_use", "use_computer", "desktop_agent", "browser_agent", "open_browser",
    "browse_web", "search_web", "navigate_site", "click_element", "type_text",
    "scroll_page", "take_screenshot", "inspect_screen", "summarize_screen",
    "open_app", "switch_app", "move_mouse", "drag_drop", "hotkey", "copy_text",
    "paste_text", "fill_form", "submit_form", "login_website", "extract_data",
    "read_document", "organize_files", "manage_files", "inspect_files",
    "save_to_file", "download_file", "watch_screen", "operate_browser",
    "control_pc", "computer_operator", "assistant_operator"
}


def _handle_extended_feature(action: str, description: str, language: str, output_path: str,
                             file_path: str, code: str, args: list, timeout: int,
                             player=None, speak=None) -> str:
    normalized = _normalize_action(action)
    feature_label = _EXTRA_FEATURES.get(normalized, normalized.replace("_", " ").title())
    task = description or feature_label

    if normalized in _COMPUTER_USE_FEATURES:
        return _write_action(
            f"Use the computer like an autonomous ChatGPT-style operator to complete: {task}. "
            "Open apps, browse, inspect the screen, click, type, scroll, and complete the workflow safely.",
            language,
            output_path,
            player,
        )

    if normalized in {
        "review_code", "review_security", "diagnose_issue", "debug_code",
        "trace_error", "analyze_performance", "inspect_runtime", "inspect_memory",
        "inspect_logs", "summarize_logs", "explain_architecture"
    }:
        if file_path or code:
            return _explain_action(file_path, code, player)
        return _write_action(f"Provide a concise analysis and practical fix for: {task}", language, output_path, player)

    if normalized in {
        "refactor_code", "refactor_module", "clean_code", "simplify_logic",
        "optimize_query", "optimize_database", "optimize_performance",
        "decompose_component", "reduce_complexity", "remove_dead_code",
        "improve_types", "improve_readability"
    }:
        if file_path or code:
            return _optimize_action(file_path, code, language, output_path, player)
        return _write_action(f"Refactor and optimize: {task}", language, output_path, player)

    if normalized in {
        "generate_readme", "generate_docs", "generate_api_docs", "generate_architecture",
        "document_api", "document_module", "document_feature", "document_service",
        "document_process", "generate_changelog", "generate_release_notes"
    }:
        return _write_action(f"Write clear documentation for: {task}", language, output_path, player)

    if normalized in {
        "test_code", "generate_tests", "create_unit_tests", "create_integration_tests",
        "create_e2e_tests", "add_coverage", "mock_dependencies", "fix_tests",
        "run_tests", "validate_build", "lint_code", "format_code"
    }:
        if normalized in {"run_tests", "validate_build"} and file_path:
            return _run_action(file_path, args, timeout, player)
        if file_path:
            return _edit_action(file_path, f"{task}. Improve correctness, resilience, and coverage while preserving intent.", player)
        return _write_action(f"Generate or fix validation coverage for: {task}", language, output_path, player)

    if normalized in {
        "convert_code", "migrate_code", "port_app", "modernize_code",
        "upgrade_dependencies", "generate_migration"
    }:
        if file_path:
            return _edit_action(file_path, f"{task}. Update the code to the new target with compatibility in mind.", player)
        return _write_action(f"Migrate or convert: {task}", language, output_path, player)

    if normalized in {"scan_vulnerabilities", "generate_security_audit"}:
        if file_path or code:
            return _explain_action(file_path, code, player)
        return _write_action(f"Audit security and harden: {task}", language, output_path, player)

    if normalized in {
        "generate_api", "generate_backend", "generate_frontend", "generate_fullstack",
        "generate_cli", "generate_dashboard", "generate_website", "generate_webapp",
        "generate_mobile_app", "generate_desktop_app", "generate_game", "generate_script",
        "generate_automation", "generate_scraper", "generate_bot", "generate_chatbot",
        "generate_ml_model", "generate_data_pipeline", "generate_etl", "generate_sql_query",
        "generate_regex", "generate_rest_api", "generate_graphql_api", "generate_microservice",
        "generate_crud", "generate_auth_system", "generate_payment_integration",
        "generate_email_service", "generate_notification_service", "generate_analytics_module",
        "generate_reporting_module", "generate_monitoring", "generate_logging", "generate_cache_layer",
        "generate_caching", "generate_cache", "generate_dockerfile", "generate_kubernetes_manifest",
        "generate_ci_pipeline", "generate_cd_pipeline", "generate_makefile", "generate_requirements",
        "generate_package_json", "generate_pyproject", "generate_vscode_settings", "generate_config",
        "generate_env_example", "generate_error_handler", "generate_backup_plan", "generate_monitoring_alerts",
        "generate_observability", "generate_schema", "generate_contract", "generate_data_model",
        "generate_benchmark", "generate_cli_tool", "generate_component", "generate_plugin",
        "generate_adapter", "generate_wrapper", "generate_seed_data", "generate_templates",
        "generate_validation", "generate_schemas", "generate_forms", "generate_tables",
        "generate_query_builder", "generate_config_loader", "generate_cache_strategy",
        "generate_job_queue", "generate_event_bus", "generate_state_machine", "generate_workflow",
        "generate_realtime_feature", "generate_search_index", "generate_filtering",
        "generate_sorting", "generate_pagination", "generate_access_control",
        "generate_error_reporting", "generate_localization", "generate_import_export",
        "generate_reconciliation", "generate_cache_warmer", "generate_metrics",
        "generate_audit_log", "generate_feature_flag", "generate_task_runner",
        "generate_worker_pool", "generate_retry_logic", "generate_retry", "generate_healthcheck",
        "create_prototype", "diagram_flow", "create_ui_mock", "create_wireframe"
    }:
        return _write_action(f"Implement the requested {feature_label}: {task}", language, output_path, player)

    return _write_action(f"Perform the requested feature task: {task}", language, output_path, player)


def code_helper(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
    speak=None
) -> str:
    """
    Called from main.py.

    parameters:
        action      : write | edit | explain | run | build | screen_debug | optimize | auto
        description : What the code should do / what change to make / what problem to analyze
        language    : Programming language (default: python)
        output_path : Where to save — user specifies full path or filename
        file_path   : Path to existing file (edit / explain / run / build / optimize)
        code        : Raw code string (explain/optimize without a file)
        args        : CLI argument list for run/build
        timeout     : Execution timeout in seconds (default: 30)
    """
    p           = parameters or {}
    action      = p.get("action", "auto").lower().strip()
    description = p.get("description", "").strip()
    language    = p.get("language", "python").strip()
    output_path = p.get("output_path", "").strip()
    file_path   = p.get("file_path", "").strip()
    code        = p.get("code", "").strip()
    args        = p.get("args", [])
    timeout     = int(p.get("timeout", 30))

    if action == "auto":
        action = _detect_intent(description, file_path, code)
        print(f"[Code] 🤖 Auto-detected: {action}")

    if action == "write":
        return _write_action(description, language, output_path, player)

    elif action == "edit":
        return _edit_action(
            file_path,
            description or p.get("instruction", ""),
            player
        )

    elif action == "explain":
        return _explain_action(file_path, code, player)

    elif action == "run":
        return _run_action(file_path, args, timeout, player)

    elif action == "build":
        return _build(description, language, output_path, args, timeout, speak, player)

    elif action == "optimize":
        return _optimize_action(file_path, code, language, output_path, player)

    elif action == "screen_debug":
        return _screen_debug_action(description, file_path, player, speak)

    else:
        normalized_action = _normalize_action(action)
        if normalized_action in _EXTRA_FEATURES or action in _FEATURE_ALIASES:
            return _handle_extended_feature(
                action,
                description,
                language,
                output_path,
                file_path,
                code,
                args,
                timeout,
                player,
                speak,
            )
        return (
            f"Unknown action: '{action}'. Use write, edit, explain, run, build, "
            "optimize, screen_debug, or any supported feature shortcut."
        )


# ── Tool declaration (auto-discovered by core/action_loader.py) ──────────────
TOOL = {
    "name": "code_helper",
    "description": "Writes, edits, explains, runs, builds, and handles 100+ code feature shortcuts.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "write | edit | explain | run | build | optimize | screen_debug | auto | computer use shortcuts such as computer_use, use_computer, browse_web, open_browser, inspect_screen, take_screenshot, click_element, type_text, scroll_page, open_app, fill_form, submit_form, login_website, manage_files, extract_data, organize_files, generate_api, refactor_code, generate_readme, test_code, scan_vulnerabilities, convert_code, create_prototype"
            },
            "description": {
                "type": "STRING",
                "description": "What the code should do or what change to make"
            },
            "language": {
                "type": "STRING",
                "description": "Programming language (default: python)"
            },
            "output_path": {
                "type": "STRING",
                "description": "Where to save the file"
            },
            "file_path": {
                "type": "STRING",
                "description": "Path to existing file for edit/explain/run/build"
            },
            "code": {
                "type": "STRING",
                "description": "Raw code string for explain"
            },
            "args": {
                "type": "STRING",
                "description": "CLI arguments for run/build"
            },
            "timeout": {
                "type": "INTEGER",
                "description": "Execution timeout in seconds (default: 30)"
            }
        },
        "required": [
            "action"
        ]
    },
    "handler": code_helper,
}
