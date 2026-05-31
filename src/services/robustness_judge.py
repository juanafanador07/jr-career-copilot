"""
Auditor de robustez: detecta alucinaciones, inconsistencias y compliance ético
en el CV optimizado comparándolo con el perfil original del candidato.
"""

import json
import os
import sys
from pathlib import Path

import yaml
from google import genai
from google.genai import types

from models import OptimizedCV, ReporteRobustez

DEFAULT_REPORT_PATH = "output/robustness_report.json"
MODEL_ID = "gemini-2.5-flash"


class RobustnessJudgeService:
    """
    Compara el CV optimizado contra el perfil YAML original y emite un reporte
    estructurado de honestidad usando salidas JSON de Gemini.
    """

    def __init__(
        self,
        profile: dict,
        optimized_cv: OptimizedCV,
        job_description: str,
        report_path: str = DEFAULT_REPORT_PATH,
        lang: str = "es",
    ) -> None:
        self.profile = profile
        self.optimized_cv = optimized_cv
        self.job_description = job_description
        self.report_path = report_path
        self.lang = lang
        self._client: genai.Client | None = None

    def _build_audit_prompt(self) -> str:
        profile_yaml = yaml.dump(self.profile, allow_unicode=True, default_flow_style=False)
        cv_json = self.optimized_cv.model_dump_json(indent=2, ensure_ascii=False)
        language_rule = (
            "Escribe el comentario_auditor y los campos descriptivos en español."
            if self.lang == "es"
            else "Write comentario_auditor and descriptive fields in English."
        )

        return (
            "Eres un auditor senior de ética profesional y reclutamiento técnico. "
            "Tu misión es validar que un CV optimizado por IA sea 100% veraz respecto "
            "al perfil original del candidato.\n\n"
            f"{language_rule}\n\n"
            "--- CRITERIOS DE AUDITORÍA ---\n"
            "1. ALUCINACIONES: empleos, títulos, certificaciones, fechas, métricas, tecnologías "
            "o logros que NO existan en el perfil original.\n"
            "2. INCONSISTENCIAS: contradicciones entre el CV optimizado y el perfil "
            "(fechas distintas, empresas diferentes, roles inflados sin base).\n"
            "3. COMPLIANCE ÉTICO: reframing permitido vs. fabricación de datos; "
            "evalúa si el CV respeta la integridad profesional del candidato.\n\n"
            "Reglas para score_honestidad (0-100):\n"
            "- 90-100: sin alucinaciones; solo reframing legítimo.\n"
            "- 70-89: exageraciones menores o inferencias dudosas.\n"
            "- 50-69: inconsistencias moderadas o datos no verificables.\n"
            "- 0-49: alucinaciones graves o múltiples datos inventados.\n\n"
            f"--- PERFIL ORIGINAL (YAML — fuente de verdad) ---\n{profile_yaml}\n\n"
            f"--- DESCRIPCIÓN DEL PUESTO (contexto) ---\n{self.job_description}\n\n"
            f"--- CV OPTIMIZADO A AUDITAR (JSON) ---\n{cv_json}\n"
        )

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
            print("Consulta GEMINI_API_KEY_GUIDE.md o crea un archivo .env en la raíz del proyecto.")
            sys.exit(1)

        try:
            self._client = genai.Client()
        except Exception as exc:
            print("\n[ERROR] Falló la inicialización del cliente de Google GenAI:")
            print(exc)
            sys.exit(1)

        return self._client

    def run_validation(self) -> ReporteRobustez:
        """
        Ejecuta la auditoría con Gemini Structured Outputs y exporta el reporte JSON.
        """
        client = self._get_client()
        prompt = self._build_audit_prompt()

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReporteRobustez.model_json_schema(),
            temperature=0.1,
            system_instruction=(
                "Eres un auditor imparcial de CVs. Detectas alucinaciones, inconsistencias "
                "y violaciones éticas comparando el CV optimizado con el perfil original. "
                "Sé riguroso: cualquier dato no respaldado debe reportarse."
            ),
        )

        print(f"[INFO] Auditando robustez del CV con {MODEL_ID}...")

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            print("\n[ERROR] Falló la llamada a la API de Gemini:")
            print(exc)
            sys.exit(1)

        if not response.text:
            print("\n[ERROR] Gemini devolvió una respuesta vacía.")
            sys.exit(1)

        try:
            report = ReporteRobustez.model_validate_json(response.text)
        except Exception as exc:
            print("\n[ERROR] No se pudo validar el reporte de robustez:")
            print(exc)
            sys.exit(1)

        self._export_report(report)
        self._print_summary(report)
        return report

    def _export_report(self, report: ReporteRobustez) -> None:
        output_path = Path(self.report_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = json.loads(report.model_dump_json(ensure_ascii=False))
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[INFO] Reporte de robustez guardado en: '{self.report_path}'")

    def _print_summary(self, report: ReporteRobustez) -> None:
        print("\n" + "=" * 60)
        print("     REPORTE DE ROBUSTEZ — AUDITORÍA DE HONESTIDAD")
        print("=" * 60)
        print(f"Score de honestidad: {report.score_honestidad}/100")
        print(f"Alucinaciones / inconsistencias detectadas: {len(report.alucinaciones_detectadas)}")

        if report.alucinaciones_detectadas:
            print("\n--- Detalle ---")
            for idx, item in enumerate(report.alucinaciones_detectadas, start=1):
                print(f"  {idx}. [{item.severidad.upper()}] {item.dato_inventado}")
                print(f"     Línea CV: {item.linea_cv}")

        print(f"\nComentario del auditor:\n{report.comentario_auditor}")
        print("=" * 60)
