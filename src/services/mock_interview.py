"""
Entrevista técnica simulada con memoria de chat y Gemini 2.5 Flash.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from google import genai
from google.genai import types

MAX_QUESTIONS = 7
DEFAULT_TRANSCRIPT_PATH = "output/interview_transcript.md"
MODEL_ID = "gemini-2.5-flash"


class MockInterviewService:
    """
    Simula una entrevista técnica interactiva centrada en tecnologías del CV y la JD.
    Mantiene historial de mensajes (chat memory) con system_instruction persistente.
    """

    def __init__(
        self,
        profile: dict,
        job_description: str,
        transcript_path: str = DEFAULT_TRANSCRIPT_PATH,
        lang: str = "es",
    ) -> None:
        self.profile = profile
        self.job_description = job_description
        self.transcript_path = transcript_path
        self.lang = lang
        self.messages: list[dict] = []
        self.system_instruction = self._build_system_instruction()
        self.questions_asked = 0
        self._client: genai.Client | None = None
        self._started_at = datetime.now()

    def _build_system_instruction(self) -> str:
        profile_yaml = yaml.dump(self.profile, allow_unicode=True, default_flow_style=False)
        language_rule = (
            "Responde SIEMPRE en español."
            if self.lang == "es"
            else "Always respond in English."
        )

        return (
            "Eres un entrevistador técnico senior en una empresa de tecnología. "
            "Conduces una entrevista para un ingeniero junior/trainee.\n\n"
            f"{language_rule}\n\n"
            "--- REGLAS ESTRICTAS ---\n"
            "1. SOLO puedes hacer preguntas sobre tecnologías, herramientas, frameworks, "
            "lenguajes, plataformas o stacks que aparezcan explícitamente en el CV del candidato "
            "o en la descripción del puesto (JD). No preguntes sobre soft skills, salario, "
            "disponibilidad, cultura empresarial ni temas fuera del stack técnico.\n"
            "2. Cada pregunta debe profundizar en experiencia práctica, proyectos, trade-offs "
            "o conceptos de UNA tecnología concreta del CV o JD.\n"
            "3. Haz UNA sola pregunta por turno. Sé directo y profesional.\n"
            "4. No repitas la misma tecnología si ya la cubriste en una pregunta anterior.\n"
            "5. Varía entre tecnologías del CV y requisitos del JD.\n"
            "6. No inventes tecnologías que el candidato no menciona en su perfil.\n\n"
            f"--- PERFIL DEL CANDIDATO (CV / YAML) ---\n{profile_yaml}\n\n"
            f"--- DESCRIPCIÓN DEL PUESTO (JD) ---\n{self.job_description}\n"
        )

    def _feedback_instruction(self) -> str:
        return (
            "Ya hiciste las preguntas permitidas. NO hagas más preguntas.\n"
            "Entrega un feedback final estructurado con:\n"
            "1. **Fortalezas** (2-3 puntos concretos según sus respuestas)\n"
            "2. **Áreas de mejora** (2-3 puntos accionables)\n"
            "3. **Recomendaciones de estudio** (tecnologías del CV/JD a reforzar)\n"
            "4. **Veredicto general** (una frase de cierre motivador pero honesto)"
        )

    def _initial_greeting(self) -> str:
        if self.lang == "es":
            return "Hola, comencemos la entrevista técnica."
        return "Hello, let's begin the technical interview."

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

    def _call_model(self, *, closing_feedback: bool = False) -> str:
        client = self._get_client()
        instruction = self._feedback_instruction() if closing_feedback else self.system_instruction

        config = types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.7,
        )

        contents = self.messages if self.messages else self._initial_greeting()

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            print("\n[ERROR] Falló la llamada a la API de Gemini:")
            print(exc)
            sys.exit(1)

        if not response.text:
            raise ValueError("Gemini devolvió una respuesta vacía.")

        text = response.text.strip()
        self.messages.append({"role": "model", "parts": [{"text": text}]})
        return text

    def _append_user_message(self, user_input: str) -> None:
        self.messages.append({"role": "user", "parts": [{"text": user_input}]})

    def run_interactive(self) -> None:
        """
        Ejecuta la entrevista en consola: hasta 7 preguntas técnicas y cierre con feedback.
        """
        candidate_name = (
            self.profile.get("personal_info", {}).get("full_name")
            or self.profile.get("full_name")
            or "Candidato"
        )

        print("=" * 60)
        print("     ENTREVISTA TÉCNICA MOCK — JR CAREER COPILOT")
        print("=" * 60)
        print(f"Candidato: {candidate_name}")
        print(f"Preguntas máximas: {MAX_QUESTIONS} (solo tecnologías del CV y JD)")
        print("Escribe 'salir' en cualquier momento para terminar anticipadamente.\n")

        print("[Entrevistador]")
        first_question = self._call_model()
        self.questions_asked = 1
        print(first_question)
        print()

        while self.questions_asked <= MAX_QUESTIONS:
            try:
                user_input = input("[Tú] ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[INFO] Entrevista interrumpida por el usuario.")
                break

            if not user_input:
                print("[INFO] Escribe una respuesta o 'salir' para terminar.")
                continue

            if user_input.lower() in {"salir", "exit", "quit"}:
                print("[INFO] Finalizando entrevista...")
                break

            self._append_user_message(user_input)

            if self.questions_asked >= MAX_QUESTIONS:
                print("\n[Entrevistador — Feedback final]")
                feedback = self._call_model(closing_feedback=True)
                print(feedback)
                break

            print("\n[Entrevistador]")
            next_question = self._call_model()
            self.questions_asked += 1
            print(next_question)
            print()

        self.export_transcript()
        print(f"\n[INFO] Transcripción guardada en: '{self.transcript_path}'")

    def export_transcript(self) -> None:
        """
        Exporta el historial de la conversación a Markdown.
        """
        output_path = Path(self.transcript_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        candidate_name = (
            self.profile.get("personal_info", {}).get("full_name")
            or self.profile.get("full_name")
            or "Candidato"
        )
        lines = [
            "# Transcripción — Entrevista técnica mock",
            "",
            f"- **Candidato:** {candidate_name}",
            f"- **Fecha:** {self._started_at.strftime('%Y-%m-%d %H:%M')}",
            f"- **Preguntas realizadas:** {min(self.questions_asked, MAX_QUESTIONS)} / {MAX_QUESTIONS}",
            f"- **Modelo:** {MODEL_ID}",
            "",
            "---",
            "",
        ]

        role_labels = {
            "model": "Entrevistador",
            "user": "Candidato",
        }

        for entry in self.messages:
            role = entry.get("role", "unknown")
            label = role_labels.get(role, role.capitalize())
            parts = entry.get("parts") or []
            text_parts = [
                part.get("text", "")
                for part in parts
                if isinstance(part, dict) and part.get("text")
            ]
            text = "\n".join(text_parts).strip()
            if not text:
                continue
            lines.append(f"## {label}")
            lines.append("")
            lines.append(text)
            lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")
