import subprocess
import sys
import os
import importlib.metadata

# Lista de bibliotecas Python necessárias para o script principal (compatíveis com Python 3.11)
# Inclui módulos padrão e externos
REQUIRED_PACKAGES = [
    "yt-dlp>=2025.02.19",  # Pacote externo para streams do YouTube, versão mais recente até março de 2025
    "subprocess",          # Padrão: execução de comandos (placeholder, não instalável via pip)
    "re",                  # Padrão: expressões regulares
    "time",                # Padrão: manipulação de tempo
    "os",                  # Padrão: operações de sistema operacional
    "json",                # Padrão: manipulação de JSON
    "shutil",              # Padrão: operações de arquivo de alto nível
    "typing",              # Padrão: anotações de tipo
    "concurrent.futures",  # Padrão: execução paralela
    "importlib.metadata",  # Padrão: metadados de pacotes
]

# Verifica se estamos usando Python 3.11
EXPECTED_PYTHON_VERSION = (3, 11)

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
        print(f"❌ Erro ao executar '{' '.join(command)}': {e.stderr}")
        sys.exit(1)

def check_python_version():
    """Verifica se a versão do Python é 3.11."""
    current_version = sys.version_info[:2]
    if current_version != EXPECTED_PYTHON_VERSION:
        print(f"❌ Erro: Este script requer Python {EXPECTED_PYTHON_VERSION[0]}.{EXPECTED_PYTHON_VERSION[1]}, mas você está usando {current_version[0]}.{current_version[1]}")
        sys.exit(1)
    print(f"✅ Python {current_version[0]}.{current_version[1]} detectado!")

def install_python_deps():
    """Instala/atualiza pacotes Python necessários."""
    print("🔧 Atualizando pip para Python 3.11...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    print("🔧 Verificando e instalando/atualizando pacotes Python...")
    installed = {pkg.metadata["Name"].lower() for pkg in importlib.metadata.distributions()}
    # Separa pacotes padrão (não instaláveis) de pacotes externos
    external_packages = [pkg for pkg in REQUIRED_PACKAGES if not pkg.replace(".", "-") in ["subprocess", "re", "time", "os", "json", "shutil", "typing", "concurrent-futures", "importlib-metadata"]]
    missing_or_updatable = [pkg for pkg in external_packages if pkg.split(">")[0].lower() not in installed]
    
    if missing_or_updatable:
        print(f"ℹ️ Instalando/atualizando pacotes externos ausentes: {missing_or_updatable}")
        run_command([sys.executable, "-m", "pip", "install"] + missing_or_updatable)
    else:
        print("✅ Todos os pacotes externos já estão instalados!")

    # Verifica módulos padrão (não instaláveis via pip, apenas confirma presença)
    standard_modules = [pkg.replace(".", "-") for pkg in REQUIRED_PACKAGES if pkg.replace(".", "-") in ["subprocess", "re", "time", "os", "json", "shutil", "typing", "concurrent-futures", "importlib-metadata"]]
    for mod in standard_modules:
        try:
            __import__(mod.replace("-", "."))
            print(f"✅ Módulo padrão {mod} presente!")
        except ImportError:
            print(f"❌ Erro: Módulo padrão {mod} não encontrado no Python 3.11!")
            sys.exit(1)

def install_system_deps():
    """Instala dependências do sistema (ffmpeg)."""
    print("🔧 Verificando e instalando dependências do sistema...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        print("✅ FFmpeg já instalado!")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ℹ️ Instalando FFmpeg...")
        if os.name == "posix" and not os.getenv("TERMUX_VERSION"):
            run_command(["apt", "update"], sudo=True)
            run_command(["apt", "install", "-y", "ffmpeg"], sudo=True)
        elif os.getenv("TERMUX_VERSION"):
            run_command(["pkg", "install", "-y", "ffmpeg"])
        else:
            print("❌ Sistema não suportado para instalação automática de FFmpeg. Instale manualmente!")
            sys.exit(1)

def verify_installation():
    """Verifica se todas as bibliotecas e dependências estão instaladas."""
    print("🔍 Verificação final...")
    installed = {pkg.metadata["Name"].lower() for pkg in importlib.metadata.distributions()}
    external_packages = [pkg for pkg in REQUIRED_PACKAGES if not pkg.replace(".", "-") in ["subprocess", "re", "time", "os", "json", "shutil", "typing", "concurrent-futures", "importlib-metadata"]]
    for pkg in external_packages:
        pkg_name = pkg.split(">")[0].lower()
        if pkg_name not in installed:
            print(f"❌ Erro: {pkg_name} não instalado!")
            sys.exit(1)
        print(f"✅ {pkg_name} instalado com sucesso!")

    # Verifica módulos padrão
    standard_modules = [pkg.replace(".", "-") for pkg in REQUIRED_PACKAGES if pkg.replace(".", "-") in ["subprocess", "re", "time", "os", "json", "shutil", "typing", "concurrent-futures", "importlib-metadata"]]
    for mod in standard_modules:
        try:
            __import__(mod.replace("-", "."))
            print(f"✅ Módulo padrão {mod} confirmado!")
        except ImportError:
            print(f"❌ Erro: Módulo padrão {mod} não encontrado!")
            sys.exit(1)

    # Verifica FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        print(f"✅ FFmpeg instalado: {result.stdout.splitlines()[0]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Erro: FFmpeg não encontrado!")
        sys.exit(1)

def run_push_py():
    """Executa push.py com Python 3.11."""
    push_script = "push.py"
    if not os.path.exists(push_script):
        print(f"❌ Erro: {push_script} não encontrado no diretório atual!")
        sys.exit(1)
    print(f"🚀 Executando {push_script} com Python 3.11...")
    run_command([sys.executable, push_script])

def main():
    print("🚀 Iniciando configuração automática para o script principal...")
    check_python_version()
    install_python_deps()
    install_system_deps()
    verify_installation()
    run_push_py()
    print("🏁 Configuração e execução concluídas com sucesso! Todos os módulos necessários estão prontos.")

if __name__ == "__main__":
    main()