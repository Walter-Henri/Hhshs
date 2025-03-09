import subprocess
import sys
import os
import platform

REQUIRED_PACKAGES = [
    "yt_dlp",
    "requests",
    "pyppeteer",
]

SYSTEM_DEPENDENCIES = [
    "libnss3",
    "libatk1.0-0",
    "libatk-bridge2.0-0",
    "libcups2",
    "libgbm1",
    "libasound2t64",
    "libx11-xcb1",
    "libxcomposite1",
    "libxcursor1",
    "libxdamage1",
    "libxi6",
    "libxtst6",
]

def run_command(command, shell=False, check=True):
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
    print("🔧 Instalando setuptools...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run_command([sys.executable, "-m", "pip", "install", "setuptools"])

def check_and_install_system_deps():
    if platform.system() != "Linux":
        print("ℹ️ Não é Linux. Pulando dependências do sistema.")
        return

    print("🔧 Verificando dependências do sistema...")
    try:
        run_command(["apt-get", "--version"])
    except subprocess.CalledProcessError:
        print("⚠️ 'apt-get' não encontrado. Pulando.")
        return

    run_command(["sudo", "apt-get", "update", "-y"])
    
    for dep in SYSTEM_DEPENDENCIES:
        print(f"🔧 Instalando {dep}...")
        run_command(["sudo", "apt-get", "install", "-y", dep], check=False)

def check_and_install_python_deps():
    import pkg_resources
    
    print("🔧 Verificando bibliotecas Python...")
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg.replace("_", "-") not in installed]
    
    if missing:
        print(f"ℹ️ Instalando pacotes ausentes: {missing}")
        run_command([sys.executable, "-m", "pip", "install"] + missing)
    
    print("🔧 Baixando Chromium para pyppeteer...")
    # Correção: Usar "pyppeteer install" como subcomando
    run_command([sys.executable, "-m", "pyppeteer", "install"])

def verify_installation():
    import pkg_resources
    
    print("🔍 Verificando instalação...")
    installed = {pkg.key for pkg in pkg_resources.working_set}
    for pkg in REQUIRED_PACKAGES:
        pkg_name = pkg.replace("_", "-")
        if pkg_name not in installed:
            print(f"❌ Erro: {pkg} não instalado!")
            sys.exit(1)
        print(f"✅ {pkg} instalado.")

def run_push_py():
    if not os.path.exists("push.py"):
        print("❌ Erro: push.py não encontrado!")
        sys.exit(1)
    
    print("🚀 Executando push.py...")
    run_command([sys.executable, "push.py"], shell=False)

def main():
    print("🚀 Iniciando configuração...")
    
    install_setuptools()
    check_and_install_system_deps()
    check_and_install_python_deps()
    verify_installation()
    run_push_py()
    
    print("🏁 Concluído com sucesso!")

if __name__ == "__main__":
    main()