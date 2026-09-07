# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict


ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
REPORTS_DIR = ROOT_DIR / "data" / "reports"


@dataclass(frozen=True)
class PipelineStep:
    id: str
    name: str
    script: Path
    requires: list[Path] = field(default_factory=list)
    requires_any: list[Path] = field(default_factory=list)
    outputs: list[Path] = field(default_factory=list)
    metadata: Path | None = None


class StepResult(TypedDict, total=False):
    id: str
    name: str
    script: str
    status: str
    returncode: int | None
    duration_sec: float
    outputs_found: list[str]
    outputs_missing: list[str]
    metadata: str | None
    metadata_ok: bool
    pre_errors: list[str]
    error: str


def build_pipeline() -> list[PipelineStep]:
    data = ROOT_DIR / "data"
    return [
        PipelineStep(
            id="01",
            name="Geometria e infraestructuras",
            script=SCRIPTS_DIR / "01_descarga_geometria_e_infraestructuras.py",
            requires=[],
            outputs=[
                data / "geo" / "secciones_canarias.gpkg",
                data / "geo" / "pois_canarias.gpkg",
                data / "raw" / "distancias_servicios.csv",
                data / "dataset_canarias_raw.csv",
                data / "dataset_canarias.gpkg",
            ],
            metadata=data / "reports" / "01_metadata.json",
        ),
        PipelineStep(
            id="02",
            name="Censo 2021 INE",
            script=SCRIPTS_DIR / "02_descarga_censo_2021_ine.py",
            requires=[],
            outputs=[data / "processed" / "censo" / "censo2021_canarias.csv"],
            metadata=data / "reports" / "02_metadata.json",
        ),
        PipelineStep(
            id="03",
            name="ADRH renta y desigualdad",
            script=SCRIPTS_DIR / "03_descarga_adrh_renta_ine.py",
            requires=[],
            outputs=[
                data / "processed" / "adrh" / "salario_renta_canarias.gpkg",
                data / "processed" / "adrh" / "salario_renta_canarias.csv",
                data / "processed" / "adrh" / "indice_gini_canarias.gpkg",
                data / "processed" / "adrh" / "indice_gini_canarias.csv",
                data / "processed" / "adrh" / "pensiones_renta_canarias.gpkg",
                data / "processed" / "adrh" / "pensiones_renta_canarias.csv",
                data / "processed" / "adrh" / "p80p20_canarias.gpkg",
                data / "processed" / "adrh" / "p80p20_canarias.csv",
            ],
            metadata=data / "reports" / "03_metadata.json",
        ),
        PipelineStep(
            id="04",
            name="Renta media del hogar",
            script=SCRIPTS_DIR / "04_descarga_renta_media_hogar.py",
            requires=[],
            outputs=[
                data / "processed" / "renta" / "renta_media_hogar_canarias.gpkg",
                data / "processed" / "renta" / "renta_media_hogar_canarias.csv",
            ],
            metadata=data / "reports" / "04_metadata.json",
        ),
        PipelineStep(
            id="05",
            name="Poblacion y demografia",
            script=SCRIPTS_DIR / "05_poblacion_demografia.py",
            requires=[],
            outputs=[
                data / "processed" / "poblacion" / "poblacion_canarias.gpkg",
                data / "processed" / "poblacion" / "poblacion_canarias.csv",
            ],
            metadata=data / "reports" / "05_metadata.json",
        ),
        PipelineStep(
            id="06",
            name="Areas e integracion Censo 2021",
            script=SCRIPTS_DIR / "06_calculo_areas_e_integracion_censo2021.py",
            requires=[],
            requires_any=[
                data / "processed" / "poblacion" / "poblacion_canarias.gpkg",
                data / "geo" / "secciones_canarias.gpkg",
            ],
            outputs=[
                data / "outputs" / "secciones_area_censo2021.gpkg",
                data / "outputs" / "secciones_area_censo2021.csv",
            ],
            metadata=data / "reports" / "06_metadata.json",
        ),
        PipelineStep(
            id="07",
            name="Fusion final EDA/entrenamiento",
            script=SCRIPTS_DIR / "07_fusion_dataset_final.py",
            requires=[data / "geo" / "secciones_canarias.gpkg"],
            outputs=[
                data / "outputs" / "dataset_final.csv",
                data / "outputs" / "dataset_final.gpkg",
            ],
            metadata=data / "reports" / "07_metadata.json",
        ),
    ]


def is_nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def missing_paths(paths: list[Path]) -> list[str]:
    return [str(p) for p in paths if not p.exists()]


def check_step(step: PipelineStep) -> list[str]:
    errors: list[str] = []
    if not step.script.exists():
        errors.append(f"Script no encontrado: {step.script}")
    for p in missing_paths(step.requires):
        errors.append(f"Paso {step.id} requiere entrada ausente: {p}")
    if step.requires_any and all(not p.exists() for p in step.requires_any):
        alternatives = ", ".join(str(p) for p in step.requires_any)
        errors.append(f"Paso {step.id} requiere una de estas entradas: {alternatives}")
    return errors


def run_step(step: PipelineStep, timeout: float | None = None) -> StepResult:
    start = time.perf_counter()
    print(f"\n{'=' * 60}")
    print(f"[{step.id}] INICIANDO: {step.name}")
    print(f"Script: {step.script}")
    print(f"{'=' * 60}")
    try:
        proc = subprocess.run(
            [sys.executable, "-u", str(step.script)],
            cwd=str(ROOT_DIR),
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        returncode: int | None = proc.returncode
        error_msg = ""
    except FileNotFoundError as e:
        raise RuntimeError(f"Interprete Python no encontrado: {sys.executable}") from e
    except subprocess.TimeoutExpired as e:
        returncode = None
        error_msg = f"Timeout tras {timeout}s: {e}"
    except OSError as e:
        returncode = None
        error_msg = f"Fallo al lanzar subproceso: {e}"
    duration = round(time.perf_counter() - start, 2)
    produced = [str(p) for p in step.outputs if is_nonempty_file(p)]
    absent = [str(p) for p in step.outputs if str(p) not in produced]
    metadata_ok = step.metadata is None or is_nonempty_file(step.metadata)
    status = "ok" if returncode == 0 and not absent and metadata_ok and not error_msg else "error"
    marker = "OK" if status == "ok" else "ERROR"
    print(f"[{step.id}] [{marker}] {step.name} en {duration}s (exit={returncode})")
    if absent:
        print(f"[{step.id}] [WARN] Salidas ausentes o vacias: {absent}")
    if not metadata_ok:
        print(f"[{step.id}] [WARN] Metadata ausente o vacio: {step.metadata}")
    if error_msg:
        print(f"[{step.id}] [ERROR] {error_msg}")
    result: StepResult = {
        "id": step.id,
        "name": step.name,
        "script": str(step.script),
        "status": status,
        "returncode": returncode,
        "duration_sec": duration,
        "outputs_found": produced,
        "outputs_missing": absent,
        "metadata": str(step.metadata) if step.metadata else None,
        "metadata_ok": metadata_ok,
    }
    if error_msg:
        result["error"] = error_msg
    return result


def parse_args(steps: list[PipelineStep]) -> argparse.Namespace:
    valid = [s.id for s in steps]
    parser = argparse.ArgumentParser(description="Orquestador del pipeline de datos de Canarias.")
    parser.add_argument("--only", nargs="+", default=None, help=f"Ejecuta solo estos pasos: {valid}")
    parser.add_argument("--skip", nargs="+", default=[], help="Omite estos pasos.")
    parser.add_argument("--from-step", dest="from_step", default=None, help="Empieza desde este paso (inclusive).")
    parser.add_argument("--continue-on-error", action="store_true", help="No detiene el pipeline si un paso falla.")
    parser.add_argument("--check-only", action="store_true", help="Solo valida dependencias sin ejecutar.")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout en segundos por paso (ej. 3600). Sin limite por defecto.")
    return parser.parse_args()


def select_steps(
    steps: list[PipelineStep],
    only: list[str] | None,
    skip: list[str],
    from_step: str | None,
) -> list[PipelineStep]:
    valid = {s.id for s in steps}
    unknown = set(only or []) | set(skip or []) | ({from_step} if from_step else set())
    invalid = sorted(u for u in unknown if u not in valid)
    if invalid:
        raise ValueError(f"Pasos desconocidos: {invalid}. Validos: {sorted(valid)}")
    selected = list(steps)
    if only:
        selected = [s for s in selected if s.id in only]
    if from_step:
        ids = [s.id for s in selected]
        selected = selected[ids.index(from_step):]
    if skip:
        selected = [s for s in selected if s.id not in skip]
    return selected


def main() -> None:
    steps = build_pipeline()
    args = parse_args(steps)
    try:
        selected = select_steps(steps, args.only, args.skip, args.from_step)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    if not selected:
        print("[WARN] No hay pasos seleccionados.")
        sys.exit(0)

    print(f"Pasos a ejecutar: {[s.id for s in selected]}")
    pre_errors: dict[str, list[str]] = {}
    for step in selected:
        errors = check_step(step)
        if errors:
            pre_errors[step.id] = errors
            print(f"[{step.id}] [WARN] Dependencias sin resolver:")
            for e in errors:
                print(f"  - {e}")

    if args.check_only:
        if pre_errors:
            print("\n[ERROR] Validacion con errores.")
            sys.exit(1)
        print("\n[OK] Todas las dependencias estan resueltas.")
        return

    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"No se pudo crear {REPORTS_DIR}: {e}") from e
    pipeline_start = time.perf_counter()
    results: list[StepResult] = []
    failed = False

    for step in selected:
        errors = check_step(step)
        strict_missing = [e for e in errors if "Script no encontrado" in e or "requiere entrada ausente" in e or "requiere una de" in e]
        if strict_missing:
            print(f"[{step.id}] [ERROR] Dependencias obligatorias ausentes, se omite el paso.")
            results.append({
                "id": step.id,
                "name": step.name,
                "script": str(step.script),
                "status": "skipped",
                "returncode": None,
                "duration_sec": 0.0,
                "outputs_found": [],
                "outputs_missing": [str(p) for p in step.outputs],
                "pre_errors": strict_missing,
            })
            failed = True
            if not args.continue_on_error:
                break
            continue
        result = run_step(step, timeout=args.timeout)
        results.append(result)
        if result["status"] != "ok":
            failed = True
            if not args.continue_on_error:
                print(f"\n[ERROR] Pipeline detenido en el paso {step.id}.")
                break

    total_duration = round(time.perf_counter() - pipeline_start, 2)
    summary: dict[str, Any] = {
        "status": "error" if failed else "ok",
        "total_duration_sec": total_duration,
        "steps": results,
    }
    summary_path = REPORTS_DIR / "pipeline_execution_summary.json"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
    except OSError as e:
        raise RuntimeError(f"No se pudo escribir {summary_path}: {e}") from e

    print(f"\n{'=' * 60}")
    print("RESUMEN DEL PIPELINE")
    print(f"{'=' * 60}")
    for r in results:
        print(f"• Paso {r['id']} ({r['name']}): {r['status']} en {r['duration_sec']}s")
    print(f"Tiempo total: {total_duration}s")
    print(f"Resumen guardado en: {summary_path}")
    print(f"{'=' * 60}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
