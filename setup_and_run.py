import subprocess
import sys
import os
import platform
import threading
from queue import Queue

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
    """Executa comandos com tratamento de erro."""
    try:
        subprocess.run(
            command,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Sucesso: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e.stderr}")
        if check:
            sys.exit(1)

def install_setuptools():
    """Instala setuptools e pip atualizado."""
    print("🔧 Instalando setuptools...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run_command([sys.executable, "-m", "pip", "install", "setuptools"])

def install_system_dep(dep):
    """Instala uma única dependência do sistema (com sudo)."""
    print(f"🔧 Instalando {dep}...")
    run_command(["sudo", "apt-get", "install", "-y", dep], check=False)

def check_and_install_system_deps():
    """Pula instalação em CI ou instala dependências do sistema com sudo."""
    if os.getenv("CI"):
        print("ℹ️ Ambiente CI detectado. Pulando dependências do sistema.")
        return

    if platform.system() != "Linux":
        print("ℹ️ Não é Linux. Pulando dependências do sistema.")
        return

    print("🔧 Verificando dependências do sistema...")
    try:
        run_command(["apt-get", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ 'apt-get' não encontrado. Pulando.")
        return

    run_command(["sudo", "apt-get", "update", "-y"])
    
    threads = []
    for dep in SYSTEM_DEPENDENCIES:
        thread = threading.Thread(target=install_system_dep, args=(dep,))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

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
    """Configura Chromium para pyppeteer."""
    print("🔧 Baixando Chromium...")
    run_command([sys.executable, "-m", "pyppeteer", "install"])

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

def worker(task_queue):
    """Processa tarefas em threads."""
    while not task_queue.empty():
        try:
            func, args = task_queue.get_nowait()
            func(*args)
            task_queue.task_done()
        except Exception as e:
            print(f"❌ Erro no worker: {e}")
            sys.exit(1)

def main():
    print("🚀 Iniciando configuração com multithreading...")
    
    task_queue = Queue()
    
    # Ordem crítica das tarefas
    task_queue.put((install_setuptools, ()))
    task_queue.put((check_and_install_system_deps, ()))
    task_queue.put((install_python_deps, ()))      # ✅ Nome correto
    task_queue.put((setup_pyppeteer, ()))
    task_queue.put((verify_installation, ()))
    task_queue.put((run_push_py, ()))
    
    # Processa tarefas em threads
    threads = []
    for _ in range(4):
        thread = threading.Thread(target=worker, args=(task_queue,))
        thread.start()
        threads.append(thread)
    
    task_queue.join()
    
    for thread in threads:
        thread.join()
    
    print("🏁 Configuração concluída com sucesso!")

if __name__ == "__main__":
    main()