import yt_dlp
import re
import random
import time
from typing import List, Dict, Tuple, Optional
import requests

# Lista de User-Agents simulando diferentes navegadores
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
]

def get_random_headers() -> Dict[str, str]:
    """Retorna cabeçalhos HTTP com um User-Agent aleatório."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.youtube.com/",
    }

def limpar_titulo(titulo: str) -> str:
    """
    Remove a data e hora do final do título, se presente, e remove chaves {}.
    """
    padrao_data_hora = r'\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$'
    titulo_limpo = re.sub(padrao_data_hora, '', titulo).strip()
    return titulo_limpo.strip('{}')

def verificar_live_e_extrair_m3u8(url_canal: str, max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
    """
    Verifica se há uma live em andamento no canal e extrai o link M3U8 e o título com retries e cabeçalhos dinâmicos.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            # Configurações do yt-dlp com cabeçalhos aleatórios
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'extract_flat': False,
                'http_headers': get_random_headers(),
                # Opcional: Adicione proxies se desejar
                # 'proxy': 'http://your_proxy:port',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"Tentativa {attempt + 1}/{max_retries} - Verificando live em: {url_canal}")
                info = ydl.extract_info(url_canal, download=False)
                if not info or not info.get('is_live'):
                    print(f"Não há live em transmissão para {url_canal}.")
                    return None, None
                m3u8_url = info.get('url')
                if not m3u8_url:
                    print(f"Link M3U8 não encontrado para {url_canal}.")
                    return None, None
                titulo_original = info.get('title', 'Live do YouTube')
                titulo = limpar_titulo(titulo_original)
                print(f"Live detectada para {url_canal}!")
                print(f"Título limpo: {titulo}")
                print(f"Link M3U8: {m3u8_url}")
                return m3u8_url, titulo
        except yt_dlp.utils.DownloadError as e:
            print(f"Erro na tentativa {attempt + 1}/{max_retries} para {url_canal}: {e}")
            attempt += 1
            if attempt < max_retries:
                delay = random.uniform(2, 5)  # Delay aleatório entre 2 e 5 segundos
                print(f"Aguardando {delay:.2f} segundos antes da próxima tentativa...")
                time.sleep(delay)
            else:
                print(f"Falha após {max_retries} tentativas para {url_canal}.")
                return None, None

def formatar_extinf(tvg_logo: str, group_title: str, titulo: str, url_canal: str) -> List[str]:
    """
    Formata a entrada para a playlist M3U com um comentário contendo o link do canal e a linha #EXTINF.
    """
    comentario = f"# Canal: {url_canal}"
    extinf = f'#EXTINF:-1 tvg-logo="{tvg_logo}" group-title="{group_title}", {titulo}'
    return [comentario, extinf]

def salvar_m3u(entradas_m3u: List[str], nome_arquivo: str = "lives.m3u8") -> None:
    """
    Salva as entradas da playlist M3U em um arquivo.
    """
    if len(entradas_m3u) > 1:  # Se houver pelo menos uma live
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            for linha in entradas_m3u:
                f.write(f"{linha}\n")
        print(f"Arquivo '{nome_arquivo}' salvo com sucesso.")
    else:
        print("Nenhuma live encontrada para os canais listados.")

def atualizar_links_m3u(canais_atualizados: dict[str, str], arquivo: str = "Hhshs/TV-FIX.m3u") -> None:
    """
    Atualiza os links M3U8 no arquivo apenas para os canais com '# Canal: <URL>'.
    """
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
        print(f"Erro: O arquivo '{arquivo}' não foi encontrado.")

def main():
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

    entradas_m3u = ["#EXTM3U"]
    canais_atualizados = {}

    print("Iniciando verificação dos canais...")
    for canal in canais:
        url_canal = canal["url"]
        tvg_logo = canal["tvg-logo"]
        group_title = canal["group-title"]

        m3u8_url, titulo = verificar_live_e_extrair_m3u8(url_canal)

        if m3u8_url and titulo:
            linhas_extinf = formatar_extinf(tvg_logo, group_title, titulo, url_canal)
            entradas_m3u.extend(linhas_extinf)
            entradas_m3u.append(m3u8_url)
            canais_atualizados[url_canal] = m3u8_url
            print(f"Canal {url_canal} adicionado a canais_atualizados.")

    print(f"Total de canais atualizados: {len(canais_atualizados)}")
    salvar_m3u(entradas_m3u)

    if canais_atualizados:
        print("Tentando atualizar Hhshs/TV-FIX.m3u...")
        atualizar_links_m3u(canais_atualizados)
    else:
        print("Nenhum canal atualizado, pulando atualização de Hhshs/TV-FIX.m3u.")

if __name__ == "__main__":
    main()
