import os
from datetime import datetime

ROOT = os.path.abspath(os.path.dirname(__file__))

def detect_structure():
    tree = []
    for dirpath, _, filenames in os.walk(ROOT):
        if any(ignored in dirpath for ignored in ['.git', '__pycache__', 'venv']):
            continue
        level = dirpath.replace(ROOT, "").count(os.sep)
        indent = "│   " * level + "├── "
        tree.append(f"{indent}{os.path.basename(dirpath)}/")
        subindent = "│   " * (level + 1)
        for f in filenames:
            tree.append(f"{subindent}{f}")
    return "\n".join(tree)


def create_or_update_readme():
    audit_path = os.path.join(ROOT, "audit_report.md")
    readme_path = os.path.join(ROOT, "README.md")
    if not os.path.exists(audit_path):
        print("❌ Нет audit_report.md. Сначала сгенерируй анализ через CodeGPT.")
        return

    with open(audit_path, "r", encoding="utf-8") as f:
        content = f.read()

    structure = detect_structure()
    if os.path.exists(readme_path):
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write("\n\n<!-- AI Audit Update -->\n" + content)
    else:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# README\n\n{content}")

    print("✅ README.md обновлён.")


def create_what_was_done():
    summary = "Проект проанализирован ИИ, сгенерирован audit_report.md и обновлён README.md."
    log_path = os.path.join(ROOT, "WHAT_WAS_DONE.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {summary}\n")


if __name__ == "__main__":
    create_or_update_readme()
    create_what_was_done()
