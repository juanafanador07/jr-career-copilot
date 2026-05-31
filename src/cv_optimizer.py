import os
import argparse
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env si existe
load_dotenv()

# Re-exportar de forma transparente clases, funciones y variables para asegurar 100% de retrocompatibilidad
from models import (
    ContactInfo,
    OptimizedExperience,
    OptimizedEducation,
    OptimizedCV
)
from file_io import (
    load_profile,
    load_job_description,
    save_markdown,
    save_html,
    load_json,
    save_json
)
from renderers import (
    HEADERS,
    generate_markdown,
    generate_html
)
from optimizer import optimize_cv, DEFAULT_OPTIMIZED_CV_PATH
from services.mock_interview import MockInterviewService, DEFAULT_TRANSCRIPT_PATH
from services.robustness_judge import RobustnessJudgeService, DEFAULT_REPORT_PATH

def parse_arguments() -> argparse.Namespace:
    """
    Analiza los argumentos de la línea de comandos.

    Returns:
        argparse.Namespace: Los argumentos analizados por el parser.
    """
    parser = argparse.ArgumentParser(
        description="JR Career Copilot — Optimizador de CV y herramientas de preparación laboral."
    )
    parser.add_argument(
        "-j", "--job",
        required=True,
        help="Ruta al archivo de texto plano (.txt) que contiene la descripción del trabajo/vacante."
    )
    parser.add_argument(
        "-p", "--profile",
        default="config/student_profile.yaml",
        help="Ruta al archivo de perfil YAML del ingeniero junior (por defecto: config/student_profile.yaml)."
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help=(
            "Ruta de salida: CV optimizado (.md) o transcripción de entrevista "
            f"(por defecto: output/optimized_cv.md o {DEFAULT_TRANSCRIPT_PATH})."
        )
    )
    parser.add_argument(
        "-l", "--lang",
        default="es",
        choices=["es", "en"],
        help="Idioma de salida del currículum optimizado: 'es' (español) o 'en' (inglés) (por defecto: 'es')."
    )
    parser.add_argument(
        "-t", "--template",
        default="templates/cv_template.html",
        help="Ruta a la plantilla HTML Jinja2 (por defecto: templates/cv_template.html)."
    )
    parser.add_argument(
        "--mock-interview",
        action="store_true",
        help="Ejecuta una entrevista técnica mock interactiva (tecnologías del CV y JD).",
    )
    parser.add_argument(
        "--robustness",
        action="store_true",
        help="Audita el CV optimizado: alucinaciones, inconsistencias y compliance ético.",
    )

    args = parser.parse_args()

    if args.output is None:
        if args.mock_interview:
            args.output = DEFAULT_TRANSCRIPT_PATH
        elif args.robustness:
            args.output = DEFAULT_REPORT_PATH
        else:
            args.output = DEFAULT_OPTIMIZED_CV_PATH

    return args

def run_optimize(args: argparse.Namespace) -> None:
    """
    Función de ejecución principal del optimizador.
    """
    print("=" * 60)
    print("      OPTIMIZADOR DE CV PARA INGENIEROS JUNIOR / TRAINEES   ")
    print("=" * 60)
    
    # 1. Analizar argumentos de consola
    args = parse_arguments()
    
    # 2. Cargar perfil de ingeniero junior
    print(f"[INFO] Cargando perfil del ingeniero junior desde: '{args.profile}'...")
    profile = load_profile(args.profile)
    
    # 3. Cargar descripción del trabajo
    print(f"[INFO] Cargando descripción de la oferta laboral en: '{args.job}'...")
    job_description = load_job_description(args.job)
    
    # 4. Optimizar el CV mediante la API de Gemini
    optimized_cv = optimize_cv(profile, job_description, args.lang)
    
    # 5. Generar formato Markdown
    print("[INFO] Generando representación en formato Markdown...")
    markdown_content = generate_markdown(optimized_cv, args.lang)
    
    # 6. Generar formato HTML
    print("[INFO] Generando representación en formato HTML premium...")
    html_content = generate_html(optimized_cv, args.template, args.lang)
    
    # 7. Guardar archivos finales
    md_output_path = args.output + ".md"
    save_markdown(markdown_content, md_output_path)
    
    # Derivar la ruta del archivo HTML reemplazando la extensión del output
    html_output_path = args.output + ".html"
    save_html(html_content, html_output_path)
    
    # Derivar la ruta del archivo JSON reemplazando la extensión del output
    json_output_path = args.output + ".json"
    save_json(optimized_cv.model_dump(), json_output_path)
    
    print("=" * 60)
    print("¡Proceso finalizado con éxito! Éxito en tu postulación laboral.")
    print("=" * 60)

def run_mock_interview(args: argparse.Namespace) -> None:
    """
    Ejecuta la entrevista técnica mock interactiva.
    """
    print(f"[INFO] Cargando perfil del candidato desde: '{args.profile}'...")
    profile = load_profile(args.profile)

    print(f"[INFO] Cargando descripción del puesto en: '{args.job}'...")
    job_description = load_job_description(args.job)

    service = MockInterviewService(
        profile=profile,
        job_description=job_description,
        transcript_path=args.output,
        lang=args.lang,
    )
    service.run_interactive()

def run_robustness(args: argparse.Namespace) -> None:
    """
    Optimiza el CV y ejecuta la auditoría de robustez contra el perfil original.
    """
    print("=" * 60)
    print("     AUDITOR DE ROBUSTEZ — JR CAREER COPILOT")
    print("=" * 60)

    print(f"[INFO] Cargando perfil del candidato desde: '{args.profile}'...")
    profile = load_profile(args.profile)

    print(f"[INFO] Cargando descripción del puesto en: '{args.job}'...")
    job_description = load_job_description(args.job)

    # Cargar el CV optimizado desde el archivo JSON generado previamente
    print(f"[INFO] Cargando CV optimizado desde: '{DEFAULT_OPTIMIZED_CV_PATH}'...")
    cv_path = DEFAULT_OPTIMIZED_CV_PATH + ".json"
    cv_data = load_json(cv_path)
    optimized_cv = OptimizedCV.model_validate(cv_data)

    service = RobustnessJudgeService(
        profile=profile,
        optimized_cv=optimized_cv,
        job_description=job_description,
        report_path=args.output,
        lang=args.lang,
    )
    service.run_validation()

def main() -> None:
    """
    Función de ejecución principal del CLI.
    """
    args = parse_arguments()

    if args.mock_interview:
        run_mock_interview(args)
    elif args.robustness:
        run_robustness(args)
    else:
        run_optimize(args)

if __name__ == "__main__":
    main()
