import yt_dlp
import re
import random
import time
import threading
from typing import List, Dict, Tuple, Optional
import http.client
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import asyncio
from pyppeteer import launch

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

async def generate_cookies_with_login(email: str, password: str, output_file: str = "cookies.txt") -> None:
    """Faz login no YouTube com Pyppeteer e salva os cookies."""
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        Printer.progress("Fazendo login no YouTube para gerar cookies com Pyppeteer...")
        try:
            browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = await browser.newPage()
            await page.goto("https://accounts.google.com/ServiceLogin?service=youtube")
            await page.waitForSelector("#identifierId")
            await page.type("#identifierId", email)
            await page.click("#identifierNext")
            await page.waitForTimeout(2000)
            await page.waitForSelector("input[name='password']")
            await page.type("input[name='password']", password)
            await page.click("#passwordNext")
            await page.waitForNavigation(timeout=20000)
            cookies = await page.cookies()
            await browser.close()
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for cookie in cookies:
                    if "youtube.com" in cookie["domain"]:
                        expiry = int(cookie.get("expires", 0)) if cookie.get("expires") > 0 else 0
                        secure = "TRUE" if cookie.get("secure") else "FALSE"
                        f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expiry}\t{cookie['name']}\t{cookie['value']}\n")
            Printer.success(f"Cookies gerados e salvos em '{output_file}'")
        except Exception as e:
            Printer.error(f"Falha ao fazer login e gerar cookies: {str(e)}")
            raise
    else:
        Printer.info(f"Arquivo de cookies '{output_file}' já existe e será usado.")

def filter_secure_cookies(input_file: str = "cookies.txt", output_file: str = "secure_cookies.txt") -> None:
    """Filtra cookies com Secure=True e salva em um novo arquivo."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        secure_lines = [line for line in lines if line.strip() and not line.startswith("#") and "TRUE" in line.split("\t")[3]]
        secure_lines.insert(0, "# Netscape HTTP Cookie File\n")
        if not secure_lines[1:]:
            Printer.error("Nenhum cookie seguro encontrado no arquivo 'cookies.txt'")
            raise ValueError("Arquivo de cookies vazio ou inválido")
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(secure_lines)
        Printer.success(f"Cookies seguros salvos em '{output_file}' com {len(secure_lines) - 1} entradas")
    except FileNotFoundError:
        Printer.error(f"Arquivo '{input_file}' não encontrado")
        raise

def load_proxy(file_path: str = "tst.txt") -> Optional[str]:
    """Lê a proxy do arquivo especificado e retorna ela."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            proxy = f.readline().strip()
        if proxy:
            Printer.info(f"Proxy carregada de '{file_path}': {proxy}")
            return proxy
        else:
            Printer.warning(f"Arquivo '{file_path}' está vazio")
            return None
    except FileNotFoundError:
        Printer.warning(f"Arquivo '{file_path}' não encontrado")
        return None

def load_proxies(file_path: str = "proxys.txt") -> List[str]:
    """Lê as proxies do arquivo especificado e retorna uma lista."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
        Printer.info(f"{len(proxies)} proxies carregadas de '{file_path}'")
        return proxies
    except FileNotFoundError:
        Printer.error(f"Arquivo '{file_path}' não encontrado")
        return []

def test_proxy(proxy: str) -> bool:
    """Testa se o proxy está funcional (suporta HTTP e SOCKS4)."""
    try:
        # Remove o protocolo e separa host/porta
        proxy_clean = proxy.replace("http://", "").replace("socks4://", "")
        proxy_parts = proxy_clean.split(":")
        proxy_host = proxy_parts[0]
        proxy_port = int(proxy_parts[1]) if len(proxy_parts) > 1 else 80

        # Testa a conexão via HTTPS
        conn = http.client.HTTPSConnection(proxy_host, proxy_port, timeout=5)
        conn.set_tunnel("www.youtube.com")
        conn.request("HEAD", "/")
        response = conn.getresponse()
        conn.close()
        return 200 <= response.status < 400
    except ValueError as e:
        Printer.debug(f"Proxy {proxy} falhou: {str(e)}")
        return False
    except Exception as e:
        Printer.debug(f"Proxy {proxy} falhou: {str(e)}")
        return False

def get_working_proxy(proxies: List[str]) -> Optional[str]:
    """Encontra a primeira proxy funcional e retorna ela."""
    Printer.progress("Testando proxies disponíveis...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                if future.result():
                    Printer.success(f"Primeira proxy ativa: {proxy}")
                    save_working_proxy(proxy)
                    return proxy
            except Exception as e:
                Printer.debug(f"Erro ao testar proxy {proxy}: {str(e)}")
    Printer.warning("Nenhum proxy funcional encontrado")
    return None

def save_working_proxy(proxy: str, file_path: str = "tst.txt") -> None:
    """Salva a proxy funcional em um arquivo."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"{proxy}\n")
    Printer.success(f"Proxy salva em '{file_path}'")

def limpar_titulo(titulo: str) -> str:
    """Remove data/hora e chaves do título."""
    padrao_data_hora = r'\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$'
    return re.sub(padrao_data_hora, '', titulo).strip('{}')

def verificar_live_e_extrair_m3u8(url_canal: str, proxy: Optional[str], max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
    """Verifica live com tratamento de erros robusto."""
    attempt = 0
    secure_cookies_file = "secure_cookies.txt"

    while attempt < max_retries:
        try:
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'no_warnings': False,
                'ignoreerrors': True,
                'http_headers': get_random_headers(),
                'cookies': secure_cookies_file,
                'socket_timeout': 15,
                'proxy': proxy or None,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                Printer.info(f"Tentativa {attempt+1}/{max_retries} | 📡 Verificando: {url_canal}")
                info = ydl.extract_info(url_canal, download=False)
                
                if not info or not info.get('is_live'):
                    Printer.warning(f"🔴 Live offline: {url_canal}")
                    return None, None
                
                if not (m3u8_url := info.get('url')):
                    Printer.error(f"❓ Link M3U8 não encontrado: {url_canal}")
                    return None, None
                
                titulo = limpar_titulo(info.get('title', 'Live YouTube'))
                Printer.success(f"🎥 Live detectada: {titulo}")
                return m3u8_url, titulo

        except Exception as e:
            Printer.error(f"Tentativa {attempt+1} falhou: {str(e)}")
            attempt += 1
            if attempt < max_retries:
                time.sleep(random.uniform(1, 3))
    
    Printer.error(f"❌ Falha final após {max_retries} tentativas: {url_canal}")
    return None, None

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
    
    # Credenciais da conta Google nova (substitua pelos seus valores)
    GOOGLE_EMAIL = "enzoprogeme22@gmail.com"
    GOOGLE_PASSWORD = "enzoprogemefrifrai123"

    # Gera cookies com login automático usando Pyppeteer
    try:
        asyncio.run(generate_cookies_with_login(GOOGLE_EMAIL, GOOGLE_PASSWORD))
        filter_secure_cookies()
    except Exception as e:
        Printer.error(f"Abortando execução devido a erro nos cookies: {str(e)}")
        return

    # Tenta carregar e testar a proxy de "tst.txt" primeiro
    tst_proxy = load_proxy("tst.txt")
    if tst_proxy:
        if test_proxy(tst_proxy):
            proxy = tst_proxy
            Printer.success(f"Proxy funcional encontrada em 'tst.txt': {proxy}. Usando-a.")
        else:
            Printer.warning(f"Proxy de 'tst.txt' ({tst_proxy}) não está funcional. Testando proxies de 'proxys.txt'...")
            proxies = load_proxies("proxys.txt")
            if not proxies:
                Printer.error("Nenhuma proxy encontrada em 'proxys.txt'. Abortando.")
                return
            proxy = get_working_proxy(proxies)
            if not proxy:
                Printer.error("Nenhum proxy funcional encontrado em 'proxys.txt'. Abortando.")
                return
    else:
        proxies = load_proxies("proxys.txt")
        if not proxies:
            Printer.error("Nenhuma proxy encontrada em 'proxys.txt'. Abortando.")
            return
        proxy = get_working_proxy(proxies)
        if not proxy:
            Printer.error("Nenhum proxy funcional encontrado em 'proxys.txt'. Abortando.")
            return

    canais = [
        {
            "url": "https://m.youtube.com/@SBTRP/live",
            "tvg-logo": "https://www.sbt.com.br/assets/images/logo-sbt.webp",
            "group-title": "🌍 TV Aberta"
        }
    ]

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(
            verificar_live_e_extrair_m3u8,
            canal["url"],
            proxy
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