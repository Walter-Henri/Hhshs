import yt_dlp
import re
import random
import time
import threading
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import subprocess

# Códigos ANSI para cores
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# Classe para prints estilizados
class Printer:
    @staticmethod
    def success(msg: str):
        print(f"{Colors.GREEN}✅ [SUCESSO] {msg}{Colors.RESET}")

    @staticmethod
    def warning(msg: str):
        print(f"{Colors.YELLOW}⚠️ [ATENÇÃO] {msg}{Colors.RESET}")

    @staticmethod
    def error(msg: str):
        print(f"{Colors.RED}❌ [ERRO] {msg}{Colors.RESET}")

    @staticmethod
    def info(msg: str):
        print(f"{Colors.CYAN}ℹ️ [INFO] {msg}{Colors.RESET}")

    @staticmethod
    def progress(msg: str):
        print(f"{Colors.MAGENTA}⌛ [PROGRESSO] {msg}{Colors.RESET}")

    @staticmethod
    def debug(msg: str):
        print(f"{Colors.BLUE}🐛 [DEBUG] {msg}{Colors.RESET}")

# Lista de User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Edg/128.0.0.0",
]

def get_random_headers() -> Dict[str, str]:
    """Retorna cabeçalhos HTTP com User-Agent aleatório e Accept-Language em pt-BR."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.youtube.com/",
    }

def verificar_live_e_extrair_m3u8(url_canal: str, username: str, password: str, max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
    """Verifica live e extrai o URL M3U8 usando yt-dlp com username e password."""
    attempt = 0
    while attempt < max_retries:
        try:
            Printer.info(f"Tentativa {attempt+1}/{max_retries} | 📡 Verificando: {url_canal}")
            # Monta o comando yt-dlp
            command = [
                "yt-dlp",
                "--username", username,
                "--password", password,
                "--get-url",
                "--format", "best",
                url_canal
            ]

            # Executa o comando e captura a saída
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            m3u8_url = result.stdout.strip()

            if not m3u8_url or "m3u8" not in m3u8_url:
                Printer.warning(f"🔴 Live offline ou URL inválido: {url_canal}")
                return None, None

            # Extrai o título usando yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'get_title': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_canal, download=False)
                titulo = limpar_titulo(info.get('title', 'Live YouTube')) if info else 'Live YouTube'

            Printer.success(f"🎥 Live detectada: {titulo}")
            return m3u8_url, titulo

        except subprocess.CalledProcessError as e:
            Printer.error(f"Tentativa {attempt+1} falhou: {e.stderr}")
            attempt += 1
            if attempt < max_retries:
                time.sleep(random.uniform(1, 3))
        except Exception as e:
            Printer.error(f"Tentativa {attempt+1} falhou: {str(e)}")
            attempt += 1
            if attempt < max_retries:
                time.sleep(random.uniform(1, 3))
    
    Printer.error(f"❌ Falha final após {max_retries} tentativas: {url_canal}")
    return None, None

def limpar_titulo(titulo: str) -> str:
    """Remove data/hora e chaves do título."""
    padrao_data_hora = r'\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$'
    return re.sub(padrao_data_hora, '', titulo).strip('{}')

def formatar_extinf(tvg_logo: str, group_title: str, titulo: str, url_canal: str) -> List[str]:
    """Formata entrada M3U."""
    return [
        f"# Canal: {url_canal}",
        f'#EXTINF:-1 tvg-logo="{tvg_logo}" group-title="{group_title}", {titulo}'
    ]

def salvar_m3u(entradas_m3u: List[str], nome_arquivo: str = "lives.m3u8") -> None:
    """Salva playlist M3U."""
    if len(entradas_m3u) > 1:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            for linha in entradas_m3u:
                f.write(f"{linha}\n")
        Printer.success(f"Arquivo '{nome_arquivo}' salvo com sucesso")
    else:
        Printer.warning("Nenhuma live encontrada para os canais listados")

def atualizar_links_m3u(canais_atualizados: Dict[str, str], arquivo: str = "Hhshs/TV-FIX.m3u") -> None:
    """Atualiza links M3U8 no arquivo."""
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        novas_linhas = []
        url_canal_atual = None
        for linha in linhas:
            linha_stripped = linha.strip()
            if linha_stripped.startswith("# Canal:"):
                url_canal_atual = linha_stripped.replace("# Canal: ", "").strip()
                novas_linhas.append(linha)
            elif linha_stripped.startswith("#EXTINF:"):
                novas_linhas.append(linha)
            elif linha_stripped.startswith("https://") and url_canal_atual in canais_atualizados:
                novas_linhas.append(canais_atualizados[url_canal_atual] + "\n")
                url_canal_atual = None
            else:
                novas_linhas.append(linha)
                url_canal_atual = None
        with open(arquivo, "w", encoding="utf-8") as f:
            f.writelines(novas_linhas)
        Printer.success(f"Arquivo '{arquivo}' atualizado com sucesso")
    except FileNotFoundError:
        Printer.error(f"Arquivo '{arquivo}' não encontrado no repositório")

def main():
    """Função principal com multithreading dinâmico."""
    Printer.info("🚀 Iniciando YouTube Live Scanner")
    Printer.progress("⚙️ Inicializando sistema...")
    
    # Credenciais fixas
    USERNAME = "enzoprogeme22@gmail.com"
    PASSWORD = "enzoprogemefrifrai123"

    canais = [
        {
            "url": "https://m.youtube.com/@SBTRP/live",
            "tvg-logo": "https://www.sbt.com.br/assets/images/logo-sbt.webp",
            "group-title": "🌍 TV Aberta"
        },
        {
            "url": "https://m.youtube.com/live/ABVQXgr2LW4",
            "tvg-logo": "https://www.sbt.com.br/assets/images/logo-sbt.webp",
            "group-title": "🌍 TV Aberta"
        }    
    ]

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(
            verificar_live_e_extrair_m3u8,
            canal["url"],
            USERNAME,
            PASSWORD
        ) for canal in canais]
        
        for future, canal in zip(futures, canais):
            m3u8_url, titulo = future.result()
            if m3u8_url and titulo:
                results.append((canal, m3u8_url, titulo))

    # Processa resultados
    if results:
        Printer.success(f"🎉 Total de lives ativas: {len(results)}")
        entradas_m3u = ["#EXTM3U"]
        canais_atualizados = {}
        
        for canal, m3u8_url, titulo in results:
            linhas = formatar_extinf(
                canal["tvg-logo"],
                canal["group-title"],
                titulo,
                canal["url"]
            )
            entradas_m3u.extend(linhas)
            entradas_m3u.append(m3u8_url)
            canais_atualizados[canal["url"]] = m3u8_url
        
        salvar_m3u(entradas_m3u)
        atualizar_links_m3u(canais_atualizados)
    else:
        Printer.warning("😞 Nenhuma live ativa encontrada")

    Printer.info("🏁 Processo finalizado com sucesso")

if __name__ == "__main__":
    main()