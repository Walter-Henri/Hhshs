import yt_dlp
import re
from typing import List, Dict, Tuple, Optional

def limpar_titulo(titulo: str) -> str:
    """
    Remove a data e hora do final do título, se presente, e remove chaves {}.

    Args:
        titulo (str): Título original do vídeo.

    Returns:
        str: Título limpo sem data, hora e chaves.
    """
    padrao_data_hora = r'\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$'
    titulo_limpo = re.sub(padrao_data_hora, '', titulo).strip()
    titulo_limpo = titulo_limpo.strip('{}')
    return titulo_limpo

def verificar_live_e_extrair_m3u8(url_canal: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Verifica se há uma live em andamento no canal e extrai o link M3U8 e o título.

    Args:
        url_canal (str): URL do canal ou da live no YouTube.

    Returns:
        Tuple[Optional[str], Optional[str]]: Link M3U8 e título do vídeo se a live estiver ativa, caso contrário (None, None).
    """
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Verificando live em: {url_canal}")
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
        print(f"Erro ao verificar a live para {url_canal}: {e}")
        return None, None

def formatar_extinf(tvg_logo: str, group_title: str, titulo: str, url_canal: str) -> List[str]:
    """
    Formata a entrada para a playlist M3U com um comentário contendo o link do canal e a linha #EXTINF.

    Args:
        tvg_logo (str): URL do logo do canal.
        group_title (str): Título do grupo do canal.
        titulo (str): Título do vídeo da live.
        url_canal (str): URL do canal do YouTube.

    Returns:
        List[str]: Lista com o comentário e a linha #EXTINF formatada.
    """
    comentario = f"# Canal: {url_canal}"
    extinf = f'#EXTINF:-1 tvg-logo="{tvg_logo}" group-title="{group_title}", {titulo}'
    return [comentario, extinf]

def salvar_m3u(entradas_m3u: List[str], nome_arquivo: str = "lives.m3u8") -> None:
    """
    Salva as entradas da playlist M3U em um arquivo.

    Args:
        entradas_m3u (List[str]): Lista de linhas da playlist M3U.
        nome_arquivo (str): Nome do arquivo de saída.
    """
    if len(entradas_m3u) > 1:  # Se houver pelo menos uma live
        with open(nome_arquivo, "w") as f:
            for linha in entradas_m3u:
                f.write(f"{linha}\n")
        print(f"Arquivo '{nome_arquivo}' salvo com sucesso.")
    else:
        print("Nenhuma live encontrada para os canais listados.")

def atualizar_links_m3u(canais_atualizados: dict[str, str], arquivo: str = "TV-FIX.m3u") -> None:
    """
    Atualiza os links M3U8 no arquivo apenas para os canais com '# Canal: <URL>'.

    Args:
        canais_atualizados (dict[str, str]): Dicionário com URLs de canais (chave) e novos links M3U8 (valor).
        arquivo (str): Caminho do arquivo M3U a ser atualizado. Padrão é "TV-FIX.m3u".
    """
    try:
        # Lê o arquivo mantendo todas as linhas
        with open(arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        novas_linhas = []
        url_canal_atual = None

        # Processa cada linha do arquivo
        for linha in linhas:
            linha_stripped = linha.strip()
            if linha_stripped.startswith("# Canal:"):
                # Armazena a URL do canal atual
                url_canal_atual = linha_stripped.replace("# Canal: ", "").strip()
                novas_linhas.append(linha)
            elif linha_stripped.startswith("#EXTINF:"):
                # Mantém a linha de metadados
                novas_linhas.append(linha)
            elif linha_stripped.startswith("https://") and url_canal_atual in canais_atualizados:
                # Substitui o link M3U8 pelo novo link do dicionário
                novas_linhas.append(canais_atualizados[url_canal_atual] + "\n")
                url_canal_atual = None  # Reseta após a substituição
            else:
                # Mantém linhas em branco ou links de canais sem '# Canal:'
                novas_linhas.append(linha)
                url_canal_atual = None  # Reseta para evitar interferência

        # Escreve o arquivo atualizado
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
    canais_atualizados = {}  # Dicionário para armazenar URLs dos canais e seus novos links M3U8

    for canal in canais:
        url_canal = canal["url"]
        tvg_logo = canal["tvg-logo"]
        group_title = canal["group-title"]

        m3u8_url, titulo = verificar_live_e_extrair_m3u8(url_canal)

        if m3u8_url and titulo:
            linhas_extinf = formatar_extinf(tvg_logo, group_title, titulo, url_canal)
            entradas_m3u.extend(linhas_extinf)
            entradas_m3u.append(m3u8_url)
            canais_atualizados[url_canal] = m3u8_url  # Armazena o novo link M3U8

    salvar_m3u(entradas_m3u)
    
    # Após salvar o arquivo lives.m3u8, atualiza o TV-FIX.m3u
    if canais_atualizados:
        atualizar_links_m3u(canais_atualizados)

if __name__ == "__main__":
    main()
