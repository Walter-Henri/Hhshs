import subprocess
import sys
import pkg_resources
import os
import platform

# Lista de bibliotecas Python necessárias
REQUIRED_PACKAGES = [
    "yt_dlp",
    "requests",
    "pyppeteer",
]

# Dependências do sistema para pyppeteer (Ubuntu/GitHub Actions)
SYSTEM_DEPENDENCIES = [
    "libnss3",
    "libatk1.0-0",
    "libatk-bridge2.0-0",
    "libcups2",
    "libgbm1",
    "libasound2",
]

def run_command(command, shell=False):
    """Executa um comando no terminal e retorna a saída ou erro."""
    try:
        process = subprocess.run(
            command,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Sucesso: {' '.join(command if not shell else [command])}")
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar {' '.join(command if not shell else [command])}: {e.stderr}")
        sys.exit(1)

def check_and_install_system_deps():
    """Verifica e instala dependências do sistema (apenas em Linux)."""
    if platform.system() != "Linux":
        print("ℹ️ Não é Linux. Pulando instalação de dependências do sistema.")
        return

    print("🔧 Verificando e instalando dependências do sistema...")
    # Verifica se 'apt-get' está disponível (Ubuntu/GitHub Actions)
    try:
        run_command(["apt-get", "--version"])
    except subprocess.CalledProcessError:
        print("⚠️ 'apt-get' não encontrado. Pulando dependências do sistema (pode ser necessário instalar manualmente).")
        return

    # Atualiza o índice de pacotes
    run_command(["sudo", "apt-get", "update", "-y"])
    
    # Instala dependências do sistema
    run_command(["sudo", "apt-get", "install", "-y"] + SYSTEM_DEPENDENCIES)

def check_and_install_python_deps():
    """Verifica e instala bibliotecas Python necessárias."""
    print("🔧 Verificando e instalando bibliotecas Python...")
    
    # Atualiza o pip
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Verifica quais pacotes já estão instalados
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg.replace("_", "-") not in installed]
    
    if missing:
        print(f"ℹ️ Instalando pacotes ausentes: {missing}")
        run_command([sys.executable, "-m", "pip", "install"] + missing)
    else:
        print("✅ Todas as bibliotecas Python já estão instaladas.")
    
    # Instala o Chromium para pyppeteer
    print("🔧 Baixando Chromium para pyppeteer...")
    run_command([sys.executable, "-m", "pyppeteer.install"])

def verify_installation():
    """Verifica se todas as bibliotecas estão instaladas."""
    print("🔍 Verificando instalação...")
    installed = {pkg.key for pkg in pkg_resources.working_set}
    for pkg in REQUIRED_PACKAGES:
        if pkg.replace("_", "-") not in installed:
            print(f"❌ Erro: {pkg} não está instalado!")
            sys.exit(1)
        else:
            print(f"✅ {pkg} instalado.")

def run_push_py():
    """Executa o script push.py."""
    if not os.path.exists("push.py"):
        print("❌ Erro: push.py não encontrado no diretório atual!")
        sys.exit(1)
    
    print("🚀 Executando push.py...")
    run_command([sys.executable, "push.py"], shell=False)

def main():
    print("🚀 Iniciando configuração e execução...")
    
    # Instala dependências do sistema (se Linux)
    check_and_install_system_deps()
    
    # Instala bibliotecas Python
    check_and_install_python_deps()
    
    # Verifica a instalação
    verify_installation()
    
    # Executa push.py
    run_push_py()
    
    print("🏁 Processo concluído com sucesso!")

if __name__ == "__main__":
    main()