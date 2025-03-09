import subprocess
import sys
import os
import importlib.metadata

# Lista de bibliotecas Python necessárias
REQUIRED_PACKAGES = [
    "yt-dlp",  # Nome correto no PyPI
    "requests",
    "pyppeteer",
]

def run_command(command, shell=False, sudo=False):
    """Executa comandos com ou sem sudo e tratamento de erro."""
    if sudo and not os.getenv("TERMUX_VERSION"):
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

def install_python_deps():
    """Instala pacotes Python necessários."""
    print("🔧 Atualizando pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    print("🔧 Verificando e instalando pacotes Python...")
    installed = {pkg.metadata["Name"].lower() for pkg in importlib.metadata.distributions()}
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg.lower() not in installed]
    
    if missing:
        print(f"ℹ️ Instalando pacotes ausentes: {missing}")
        run_command([sys.executable, "-m", "pip", "install"] + missing)
    else:
        print("✅ Todos pacotes Python já estão instalados.")

def setup_pyppeteer():
    """Configura Chromium para pyppeteer."""
    print("🔧 Baixando Chromium...")
    run_command(["pyppeteer-install"])

def verify_installation():
    """Verifica se todas as bibliotecas estão instaladas."""
    print("🔍 Verificação final...")
    installed = {pkg.metadata["Name"].lower() for pkg in importlib.metadata.distributions()}
    for pkg in REQUIRED_PACKAGES:
        if pkg.lower() not in installed:
            print(f"❌ Erro: {pkg} não instalado!")
            sys.exit(1)
        print(f"✅ {pkg} instalado.")

def run_push_py():
    """Executa push.py com sudo no GitHub Actions."""
    if not os.path.exists("push.py"):
        print("❌ Erro: push.py não encontrado!")
        sys.exit(1)
    print("🚀 Executando push.py...")
    run_command([sys.executable, "push.py"], sudo=True)

def main():
    print("🚀 Iniciando configuração...")
    install_python_deps()
    setup_pyppeteer()
    verify_installation()
    run_push_py()
    print("🏁 Configuração concluída com sucesso!")

if __name__ == "__main__":
    main()