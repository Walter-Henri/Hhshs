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
    print("🔧 Iniciando instalação do setuptools...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run_command([sys.executable, "-m", "pip", "install", "setuptools"])

def install_system_dep(dep):
    """Instala uma única dependência do sistema."""
    print(f"🔧 Instalando {dep}...")
    run_command(["sudo", "apt-get", "install", "-y", dep], check=False)

def check_and_install_system_deps():
    """Instala dependências do sistema em paralelo."""
    if platform.system() != "Linux":
        print("ℹ️ Não é Linux. Pulando dependências do sistema.")
        return

    try:
        run_command(["apt-get", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ 'apt-get' não encontrado. Pulando.")
        return

    run_command(["sudo", "apt-get", "update", "-y"])
    
    # Usar threads para instalar dependências em paralelo
    threads = []
    for dep in SYSTEM_DEPENDENCIES:
        thread = threading.Thread(target=install_system_dep, args=(dep,))
        thread.start()
        threads.append(thread)
    
    # Aguardar todas as threads finalizarem
    for thread in threads:
        thread.join()

def check_python_deps():
    """Verifica dependências Python ausentes."""
    import pkg_resources
    installed = {pkg.key for pkg in pkg_resources.working_set}
    return [pkg for pkg in REQUIRED_PACKAGES if pkg.replace("_", "-") not in installed]

def install_python_deps(packages):
    """Instala pacotes Python em lote."""
    if packages:
        print(f"🔧 Instalando pacotes Python: {packages}")
        run_command([sys.executable, "-m", "pip", "install"] + packages)

def check_and_install_python_deps():
    """Gerencia instalação de dependências Python."""
    print("🔍 Verificando pacotes Python...")
    missing = check_python_deps()
    if missing:
        install_python_deps(missing)
    else:
        print("✅ Todos pacotes Python estão instalados.")

def setup_pyppeteer():
    """Configura pyppeteer (Chromium)."""
    print("🔧 Baixando Chromium para pyppeteer...")
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
    """Executa o script principal."""
    if not os.path.exists("push.py"):
        print("❌ Erro: push.py não encontrado!")
        sys.exit(1)
    print("🚀 Executando push.py...")
    run_command([sys.executable, "push.py"])

def worker(task_queue):
    """Worker para processar tarefas em threads."""
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
    
    # Fila de tarefas sequenciais
    task_queue = Queue()
    
    # Adicionar tarefas na ordem correta
    task_queue.put((install_setuptools, ()))
    task_queue.put((check_and_install_system_deps, ()))
    task_queue.put((check_and_install_python_deps, ()))
    task_queue.put((setup_pyppeteer, ()))
    task_queue.put((verify_installation, ()))
    task_queue.put((run_push_py, ()))
    
    # Criar threads para processar a fila
    threads = []
    for _ in range(4):  # Número de threads simultâneas
        thread = threading.Thread(target=worker, args=(task_queue,))
        thread.start()
        threads.append(thread)
    
    # Aguardar conclusão de todas as tarefas
    task_queue.join()
    
    # Parar threads após conclusão
    for thread in threads:
        thread.join()
    
    print("🏁 Configuração concluída com sucesso!")

if __name__ == "__main__":
    main()