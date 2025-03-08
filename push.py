import yt_dlp
import re
import random
import time
from typing import List, Dict, Tuple, Optional
import http.client  # Biblioteca padrão para testar proxies

# Lista de User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",  # Chrome 128 (2024)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # Chrome 91
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",  # Safari 14
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",  # Firefox 89
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Edg/128.0.0.0",  # Edge 128
]

# Lista de proxies brasileiros HTTP verificados como online (atualizada em 08/03/2025)
PROXIES = [
    "http://200.10.82.130:8080",    # Proxy 1 - Brasil, verificado em ProxyScrape
    "http://45.179.186.195:999",    # Proxy 2 - Brasil, verificado em FreeProxyList
    "http://177.101.226.117:8080",  # Proxy 3 - Brasil, verificado em ProxyNova
    "http://187.95.125.76:3128",    # Proxy 4 - Brasil, verificado em ProxyScrape
    "http://201.20.77.133:3128",    # Proxy 5 - Brasil, verificado em FreeProxyList
    "http://138.36.159.195:8080",   # Proxy 6 - Brasil, verificado em ProxyNova
]

def get_random_headers() -> Dict[str, str]:
    """Retorna cabeçalhos HTTP com User-Agent aleatório e Accept-Language em pt-BR."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.youtube.com/",
    }

def filter_secure_cookies(input_file: str = "cookies.txt", output_file: str = "secure_cookies.txt") -> None:
    """Filtra cookies com Secure=True e salva em um novo arquivo."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        secure_lines = [line for line in lines if line.strip() and not line.startswith("#") and "TRUE" in line.split("\t")[3]]
        secure_lines.insert(0, "# Netscape HTTP Cookie File\n")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(secure_lines)
        print(f"Cookies com Secure=True salvos em '{output_file}'.")
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        raise

def test_proxy(proxy: str) -> bool:
    """Testa se o proxy está funcional usando http.client contra o YouTube."""
    try:
        # Extrai host e porta do proxy (remove 'http://' e separa por ':')
        proxy_parts = proxy.replace("http://", "").split(":")
        proxy_host = proxy_parts[0]
        proxy_port = int(proxy_parts[1]) if len(proxy_parts) > 1 else 80

        # Testa conexão com o YouTube através do proxy
        conn = http.client.HTTPConnection(proxy_host, proxy_port, timeout=5)
        conn.set_tunnel("www.youtube.com")  # Simula requisição ao YouTube
        conn.request("HEAD", "/")
        response = conn.getresponse()
        conn.close()
        
        # Verifica se o status é 2xx ou 3xx (sucesso ou redirecionamento)
        return 200 <= response.status < 400
    except (http.client.HTTPException, ValueError, Exception) as e:
        print(f"Proxy {proxy} não está funcionando: {str(e)}")
        return False

def get_working_proxy(proxies: List[str]) -> Optional[str]:
    """Retorna o primeiro proxy funcional da lista."""
    for proxy in proxies:
        if test_proxy(proxy):
            print(f"Proxy funcional encontrado: {proxy}")
            return proxy
    print("Nenhum proxy funcional encontrado.")
    return None

def limpar_titulo(titulo: str) -> str:
    """Remove data/hora e chaves do título."""
    padrao_data_hora = r'\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$'
    return re.sub(padrao_data_hora, '', titulo).strip('{}')

def verificar_live_e_extrair_m3u8(url_canal: str, max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
    """Verifica live e extrai M3U8 com retries, cookies filtrados e proxy."""
    attempt = 0
    secure_cookies_file = "secure_cookies.txt"
    proxy = get_working_proxy(PROXIES)  # Obtém um proxy funcional antes de começar
    
    if not proxy:
        print("Sem proxy funcional disponível. Prosseguindo sem proxy (pode falhar por geolocalização).")
    
    while attempt < max_retries:
        try:
            ydl_opts = {
                'format': 'best',
                'quiet': False,  # Logs detalhados
                'no_warnings': False,
                'ignoreerrors': True,
                'extract_flat': False,
                'http_headers': get_random_headers(),
                'cookies': secure_cookies_file,
                'socket_timeout': 10,
                'proxy': proxy if proxy else None,  # Usa proxy se disponível
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"Tentativa {attempt + 1}/{max_retries} - Verificando live em: {url_canal} (Proxy: {proxy or 'Nenhum'})")
                info = ydl.extract_info(url_canal, download=False)
                if not info or not info.get('is_live'):
                    print(f"Não há live em transmissão para {url_canal}.")
                    return None, None
                m3u8_url = info.get('url')
                if not m3u8_url:
                    print(f"Link M3U8 não encontrado para {url_canal}.")
                    return None, None
                titulo = limpar_titulo(info.get('title', 'Live do YouTube'))
                print(f"Live detectada para {url_canal}! Título: {titulo}")
                return m3u8_url, titulo
        except (yt_dlp.utils.DownloadError, Exception) as e:
            print(f"Erro na tentativa {attempt + 1}/{max_retries}: {str(e)}")
            attempt += 1
            if attempt < max_retries:
                delay = random.uniform(2, 5)
                print(f"Aguardando {delay:.2f}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                print(f"Falha após {max_retries} tentativas para {url_canal}.")
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
        print(f"Arquivo '{nome_arquivo}' salvo com sucesso.")
    else:
        print("Nenhuma live encontrada para os canais listados.")

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
        print(f"Arquivo '{arquivo}' atualizado com sucesso!")
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo}' não foi encontrado no repositório.")

def main():
    """Função principal."""
    canais = [
        {
            "url": "https://m.youtube.com/@SBTRP/live",
            "tvg-logo": "https://www.sbt.com.br/assets/images/logo-sbt.webp",
            "group-title": "🌍 TV Aberta"
        }
    ]

    # Filtra cookies com Secure=True
    filter_secure_cookies()

    entradas_m3u = ["#EXTM3U"]
    canais_atualizados = {}

    print("Iniciando verificação dos canais (simulando Brasil)...")
    for i, canal in enumerate(canais):
        if i > 0:  # Intervalo de 5 segundos entre requisições
            print("Aguardando 5 segundos antes da próxima requisição...")
            time.sleep(5)
        
        url_canal = canal["url"]
        m3u8_url, titulo = verificar_live_e_extrair_m3u8(url_canal)
        if m3u8_url and titulo:
            linhas_extinf = formatar_extinf(canal["tvg-logo"], canal["group-title"], titulo, url_canal)
            entradas_m3u.extend(linhas_extinf)
            entradas_m3u.append(m3u8_url)
            canais_atualizados[url_canal] = m3u8_url
            print(f"Canal {url_canal} adicionado a canais_atualizados.")

    print(f"Total de canais com lives: {len(canais_atualizados)}")
    salvar_m3u(entradas_m3u)
    
    if canais_atualizados:
        print("Tentando atualizar Hhshs/TV-FIX.m3u...")
        atualizar_links_m3u(canais_atualizados)
    else:
        print("Nenhum canal com live ativa, pulando atualização de Hhshs/TV-FIX.m3u.")

if __name__ == "__main__":
    main()
