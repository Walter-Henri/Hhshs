import subprocess
import sys
import os

# Lista de bibliotecas Python necessárias
REQUIRED_PACKAGES = [
    "yt_dlp",
    "requests",
    "pyppeteer",
]

def run_command(command, shell=False, sudo=False):
    """Executa comandos com ou sem sudo e tratamento de erro."""
    if sudo and not os.getenv("TERMUX_VERSION"):  # Evita sudo no Termux
        command = ["sudo"] + command
    try:
        process = subprocess.run(
            command,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Sucesso: {' '.join(command)}")
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e.stderr}")
        sys.exit(1)

def install_setuptools():
    """Instala setuptools e atualiza pip."""
    print("🔧 Instalando setuptools...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run_command([sys.executable, "-m", "pip", "install", "setuptools"])

def check_python_deps():
    """Verifica pacotes Python ausentes."""
    import pkg_resources
    installed = {pkg.key for pkg in pkg_resources.working_set}
    return [pkg for pkg in REQUIRED_PACKAGES if pkg.replace("_", "-") not in installed]

def install_python_deps():
    """Instala pacotes Python ausentes."""
    missing = check_python_deps()
    if missing:
        print(f"🔧 Instalando pacotes Python: {missing}")
        run_command([sys.executable, "-m", "pip", "install"] + missing)
    else:
        print("✅ Todos pacotes Python estão instalados.")

def setup_pyppeteer():
    """Configura Chromium para pyppeteer usando pyppeteer-install."""
    print("🔧 Baixando Chromium...")
    run_command(["pyppeteer-install"])

def verify_installation():
    """Verifica instalação completa."""
    import pkg_resources
    print("🔍 Verificação final...")
    installed = {pkg.key for pkg in pkg_resources.working_set}
    for pkg in REQUIRED_PACKAGES:
        if pkg.replace("_", "-") not in installed:
            print(f"❌ Erro: {pkg} não instalado!")
            sys.exit(1)
    print("✅ Todas as dependências estão OK.")

def run_push_py():
    """Executa push.py."""
    if not os.path.exists("push.py"):
        print("❌ Erro: push.py não encontrado!")
        sys.exit(1)
    print("🚀 Executando push.py...")
    run_command([sys.executable, "push.py"])

def main():
    print("🚀 Iniciando configuração...")
    
    # Executa todas as etapas sequencialmente
    install_setuptools()
    install_python_deps()
    setup_pyppeteer()
    verify_installation()
    run_push_py()
    
    print("🏁 Configuração concluída com sucesso!")

if __name__ == "__main__":
    main()