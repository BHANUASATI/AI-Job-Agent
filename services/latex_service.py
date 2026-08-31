import subprocess
import os

def compile_resume(tex_path, output_dir):
    try:
        subprocess.run(
            [
                "pdflatex",
                f"-output-directory={output_dir}",
                tex_path
            ],
            check=True,
            capture_output=True,
            text=True
        )

        pdf_name = os.path.basename(tex_path).replace(".tex", ".pdf")
        return os.path.join(output_dir, pdf_name)

    except subprocess.CalledProcessError as e:
        print("LaTeX Compilation Failed:")
        print(e.stderr)
        return None