import subprocess
import sys
import os
import platform

# Lista de bibliotecas Python necessárias
REQUIRED_PACKAGES = [
    "yt_dlp",
    "requests",
    "pyppeteer",
]

# Dependências do sistema para pyppeteer (ajustadas para Ubuntu 22.04+)
SYSTEM_DEPENDENCIES = [
    "libnss3",
    "libatk1.0-0",
    "libatk-bridge2.0-0",
    "libcups2",
    "libgbm1",
    "libasound2t64",  # Substituído por libasound2t64 em Ubuntu 22.04+
    "libx11-xcb1",
    "libxcomposite1",
    "libxcursor1",
    "libxdamage1",
    "libxi6",
    "libxtst6",
]

def run_command(command, shell=False, check=True):
    """Executa um comando no terminal e retorna a saída ou erro."""
    try:
        process = subprocess.run(
            command,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Sucesso: {' '.join(command if not shell else [command])}")
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar {' '.join(command if not shell else [command])}: {e.stderr}")
        if check:
            sys.exit(1)
        return None

def install_setuptools():
    """Instala o setuptools como passo inicial."""
    print("🔧 Instalando setuptools (necessário para pkg_resources)...")
    run_command([sys.executable, "-m", "pip3.11", "install", "--upgrade", "pip"])
    run_command([sys.executable, "-m", "pip3.11", "install", "setuptools"])

def check_and_install_system_deps():
    """Verifica e instala dependências do sistema (apenas em Linux)."""
    if platform.system() != "Linux":
        print("ℹ️ Não é Linux. Pulando instalação de dependências do sistema.")
        return

    print("🔧 Verificando e instalando dependências do sistema...")
    try:
        run_command(["apt-get", "--version"])
    except subprocess.CalledProcessError:
        print("⚠️ 'apt-get' não encontrado. Pulando dependências do sistema.")
        return

    run_command(["sudo", "apt-get", "update", "-y"])
    
    # Instala cada dependência individualmente, ignorando falhas
    for dep in SYSTEM_DEPENDENCIES:
        print(f"🔧 Tentando instalar {dep}...")
        run_command(["sudo", "apt-get", "install", "-y", dep], check=False)

def check_and_install_python_deps():
    """Verifica e instala bibliotecas Python necessárias."""
    import pkg_resources  # Importado após setuptools estar garantido
    
    print("🔧 Verificando e instalando bibliotecas Python...")
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg.replace("_", "-") not in installed]
    
    if missing:
        print(f"ℹ️ Instalando pacotes ausentes: {missing}")
        run_command([sys.executable, "-m", "pip3.11", "install"] + missing)
    else:
        print("✅ Todas as bibliotecas Python já estão instaladas.")
    
    print("🔧 Baixando Chromium para pyppeteer...")
    run_command([sys.executable, "-m", "pyppeteer.install"])

def verify_installation():
    """Verifica se todas as bibliotecas estão instaladas."""
    import pkg_resources  # Importado após setuptools estar garantido
    
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
    
    # Instala setuptools primeiro
    install_setuptools()
    
    # Instala dependências do sistema
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