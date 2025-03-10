import subprocess
import re
import time
import os
import json
import shutil
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp

class Estilos:
    VERMELHO = '\033[38;5;196m'
    VERDE = '\033[38;5;40m'
    AMARELO = '\033[38;5;220m'
    CIANO = '\033[38;5;51m'
    MAGENTA = '\033[38;5;201m'
    RESET = '\033[0m'
    NEGRITO = '\033[1m'
    FUNDO_VERDE = '\033[48;5;28m'

class Logger:
    @staticmethod
    def cabecalho(msg: str):
        print(f"\n{Estilos.FUNDO_VERDE}{Estilos.NEGRITO} 🌟 === {msg.upper()} === 🌟 {Estilos.RESET}")

    @staticmethod
    def sucesso(msg: str):
        print(f"{Estilos.VERDE}  ✅  {msg:<60}{Estilos.RESET}")

    @staticmethod
    def aviso(msg: str):
        print(f"{Estilos.AMARELO}  ⚠️  {msg:<60}{Estilos.RESET}")

    @staticmethod
    def erro(msg: str):
        print(f"{Estilos.VERMELHO}  ❌  {msg:<60}{Estilos.RESET}")

    @staticmethod
    def processo(msg: str):
        print(f"{Estilos.MAGENTA}  ⏳  {msg:<60}{Estilos.RESET}")

    @staticmethod
    def debug(msg: str):
        print(f"{Estilos.CIANO}  🛠️  {msg:<60}{Estilos.RESET}")

    @staticmethod
    def separador():
        print(f"{Estilos.CIANO}✨ {'='*68} ✨{Estilos.RESET}")

def verificar_dependencias() -> bool:
    Logger.cabecalho("Verificação de Dependências")
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, check=True)
        Logger.sucesso(f"yt-dlp versão: {result.stdout.strip()} 🎉")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        Logger.erro(f"yt-dlp não encontrado: {str(e)} 😞")
        print(f"\n  📌 Instale com: {Estilos.NEGRITO}pip install yt-dlp{Estilos.RESET}\n")
        return False

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        Logger.sucesso("FFmpeg instalado com sucesso! 🎥")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        Logger.erro(f"FFmpeg não encontrado: {str(e)} 😞")
        print(f"\n  📌 Instale com: {Estilos.NEGRITO}sudo apt install ffmpeg{Estilos.RESET}\n")
        return False

    # Verificação opcional de ffplay e vlc
    for tool in ["ffplay", "vlc"]:
        try:
            subprocess.run([tool, "--version"], capture_output=True, text=True, check=True)
            Logger.sucesso(f"{tool} encontrado para testes! 🎮")
        except (subprocess.CalledProcessError, FileNotFoundError):
            Logger.aviso(f"{tool} não encontrado (opcional para testes) 🤔")
    return True

def testar_url(url: str, timeout: int = 15) -> bool:
    try:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", url, "-t", "5", "-f", "null", "-"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        Logger.debug(f"Teste de URL falhou: {str(e)} 🧪")
        return False
    except Exception as e:
        Logger.erro(f"Erro inesperado ao testar URL: {str(e)} 💥")
        return False

def obter_stream_com_audio(url: str, tentativas: int = 3, timeout_base: int = 20) -> Tuple[Optional[str], Optional[str]]:
    formatos_priorizados = [
        "best[height<=1080][acodec!=none][protocol=hls]",
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "best[acodec!=none]",
        "best"
    ]

    for tentativa in range(tentativas):
        for formato in formatos_priorizados:
            try:
                Logger.processo(f"Tentativa {tentativa+1}/{tentativas} - Formato: {formato} 🔍 URL: {url}")
                cmd_info = ["yt-dlp", "--dump-json", "--no-warnings", "--geo-bypass", "--force-ipv4", url]
                result = subprocess.run(cmd_info, capture_output=True, text=True, check=True, timeout=timeout_base + tentativa * 5)
                info = json.loads(result.stdout)

                Logger.debug(f"ID da live: {info.get('id')} - Ao vivo: {info.get('is_live')} 🎬")
                if not info.get('is_live'):
                    Logger.aviso(f"Live não está ativa no momento: {url} ⏸️")
                    return None, limpar_titulo(info.get('title', url.split('/')[-1]))

                cmd_url = [
                    "yt-dlp", "--get-url", "--format", formato, "--no-warnings",
                    "--geo-bypass", "--force-ipv4", "--no-cache-dir", url
                ]
                result_url = subprocess.run(cmd_url, capture_output=True, text=True, check=True, timeout=timeout_base)
                stream_url = result_url.stdout.strip()

                if not stream_url:
                    raise ValueError("URL do stream vazia")

                Logger.processo(f"Verificando URL: {stream_url[:50]}... 🔎")
                if testar_url(stream_url):
                    titulo = limpar_titulo(info.get('title', url.split('/')[-1]))
                    Logger.sucesso(f"Stream válido encontrado: {titulo} 🎉")
                    return stream_url, titulo
                else:
                    Logger.aviso(f"URL não reproduzível: {stream_url[:50]}... 🚫")

            except subprocess.CalledProcessError as e:
                erro_msg = e.stderr.strip()
                Logger.erro(f"Erro no yt-dlp: {erro_msg[:50]}... 😵")
                if "This live event will" in erro_msg:
                    Logger.aviso(f"Live agendada ou encerrada: {url} ⏰")
                    return None, limpar_titulo(url.split('/')[-1])
            except subprocess.TimeoutExpired:
                Logger.erro("Timeout na operação ⏱️")
            except json.JSONDecodeError as e:
                Logger.erro(f"Erro ao decodificar JSON: {str(e)} 📜")
            except Exception as e:
                Logger.erro(f"Falha crítica: {str(e)} 💥")
        time.sleep(3)
    
    Logger.erro(f"Falha após {tentativas} tentativas para {url} 😢")
    return None, url.split('/')[-1]

def limpar_titulo(titulo: str, manter_info: bool = False) -> str:
    if manter_info:
        return titulo.strip()
    return re.sub(
        r'(\s*(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}:\d{2})\s*)|([][{}()|])|(AO?\s?VIVO)|(LIVE)',
        '', titulo, flags=re.IGNORECASE
    ).strip()

def criar_estrutura_pastas() -> bool:
    estrutura = {"Hhshs": ["TV-FIX.m3u"], "logs": []}
    try:
        uso_disco = shutil.disk_usage(".")
        if uso_disco.free < 1024 * 1024:  # Menos de 1MB livre
            Logger.erro("Espaço em disco insuficiente! (<1MB) 💾")
            return False

        for pasta, arquivos in estrutura.items():
            os.makedirs(pasta, exist_ok=True)
            for arq in arquivos:
                caminho = os.path.join(pasta, arq)
                if not os.path.exists(caminho):
                    with open(caminho, 'w', encoding="utf-8") as f:
                        f.write("#EXTM3U\n")
        return True
    except OSError as e:
        Logger.erro(f"Falha ao criar estrutura: {str(e)} 📁")
        return False

def atualizar_playlist(canais_validos: List[Dict]) -> bool:
    Logger.cabecalho("Atualizando Playlists")
    if not criar_estrutura_pastas():
        return False

    try:
        with open("lives.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for canal in canais_validos:
                f.write(f"# Canal: {canal['original']}\n")
                f.write(f'#EXTINF:-1 tvg-logo="{canal["logo"]}" group-title="{canal["grupo"]}",{canal["titulo"]}\n')
                f.write(f"{canal['url'] if canal['url'] else 'Live não ativa'}\n")
        Logger.sucesso("Arquivo lives.m3u8 atualizado com sucesso! 📝")
    except OSError as e:
        Logger.erro(f"Erro ao escrever lives.m3u8: {str(e)} ⚠️")
        return False

    caminho_fixo = "Hhshs/TV-FIX.m3u"
    try:
        if os.path.exists(caminho_fixo):
            with open(caminho_fixo, "r", encoding="utf-8") as f:
                linhas = f.readlines()
        else:
            linhas = ["#EXTM3U\n"]

        canais_dict = {canal["original"]: canal for canal in canais_validos}
        canais_existentes = set()
        linhas_atualizadas = ["#EXTM3U\n"]
        linhas_restantes = []
        url_atual = None
        bloco_atual = []

        for linha in linhas[1:]:
            if linha.startswith("# Canal: "):
                if bloco_atual and url_atual:
                    if url_atual in canais_dict:
                        linhas_atualizadas.extend(bloco_atual)
                    else:
                        linhas_restantes.extend(bloco_atual)
                url_atual = linha.split("# Canal: ")[1].strip()
                canais_existentes.add(url_atual)
                bloco_atual = [linha]
            elif url_atual and (linha.startswith("http") or linha.startswith("Live não ativa") or linha.startswith("URL não disponível")):
                if url_atual in canais_dict:
                    novo_canal = canais_dict[url_atual]
                    bloco_atual.append(f"{novo_canal['url'] if novo_canal['url'] else 'Live não ativa'}\n")
                    Logger.debug(f"Link atualizado para {url_atual} 🔗")
                else:
                    bloco_atual.append(linha)
                if url_atual in canais_dict:
                    linhas_atualizadas.extend(bloco_atual)
                else:
                    linhas_restantes.extend(bloco_atual)
                url_atual = None
                bloco_atual = []
            else:
                if bloco_atual and url_atual:
                    if url_atual in canais_dict:
                        linhas_atualizadas.extend(bloco_atual)
                    else:
                        linhas_restantes.extend(bloco_atual)
                url_atual = None
                bloco_atual = []
                linhas_restantes.append(linha)
                Logger.debug(f"Linha preservada sem alterações: {linha.strip()} 📌")

        for canal in canais_validos:
            if canal["original"] not in canais_existentes:
                linhas_atualizadas.append(f"# Canal: {canal['original']}\n")
                linhas_atualizadas.append(f'#EXTINF:-1 tvg-logo="{canal["logo"]}" group-title="{canal["grupo"]}",{canal["titulo"]}\n')
                linhas_atualizadas.append(f"{canal['url'] if canal['url'] else 'Live não ativa'}\n")
                Logger.debug(f"Canal adicionado: {canal['original']} ➕")

        novas_linhas = linhas_atualizadas + linhas_restantes

        with open(caminho_fixo, "w", encoding="utf-8") as f:
            f.writelines(novas_linhas)
        Logger.sucesso("Arquivo TV-FIX.m3u atualizado com canais no topo! 📺")
        return True

    except OSError as e:
        Logger.erro(f"Falha ao atualizar TV-FIX.m3u: {str(e)} ⚠️")
        return False

def main():
    Logger.cabecalho("YouTube Live Audio Validator")
    if not verificar_dependencias():
        Logger.erro("Dependências ausentes, encerrando... 😞")
        return

    canais = [
        {
            "original": "https://www.youtube.com/@SBTRP/live",
            "logo": "https://www.sbt.com.br/assets/images/logo-sbt.webp",
            "grupo": "🌍 TV Aberta"
        },
        {
            "original": "https://www.youtube.com/live/ABVQXgr2LW4",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/9/98/SBT_logo.svg",
            "grupo": "🌍 TV Aberta"
        },
        {
            "original": "https://www.youtube.com/@abaleiaisis/live",
            "logo": "https://i.imgur.com/RUKVrOH.png",
            "grupo": "🌍 TV Aberta"
        },
        {
            "original": "https://www.youtube.com/@radionovasdepazoficial/live",
            "logo": "https://yt3.googleusercontent.com/N2qFz5sN9GWmwrQfJtzKcu6d6w-dmHqE3v3AlfUdB8Y0ikyn1XCxTlEcV-oaRLv7ASepJ0sTRAw=s900-c-k-c0x00ffffff-no-rj",
            "grupo": "🙏 Religioso"
        }
    ]

    Logger.separador()
    Logger.cabecalho("Processando Canais")
    resultados = []
    max_workers = min(len(canais), 5)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(obter_stream_com_audio, ch["original"]): ch for ch in canais}
            for future in as_completed(futures):
                canal = futures[future]
                try:
                    url, titulo = future.result()
                    resultados.append({
                        "original": canal["original"],
                        "url": url,
                        "titulo": titulo,
                        "logo": canal["logo"],
                        "grupo": canal["grupo"]
                    })
                except Exception as e:
                    Logger.erro(f"Erro ao processar {canal['original']}: {str(e)} 😓")
                Logger.separador()
    except Exception as e:
        Logger.erro(f"Falha no processamento paralelo: {str(e)} 💥")
        return

    if resultados:
        if atualizar_playlist(resultados):
            Logger.sucesso(f"Total de streams processados: {len(resultados)} 📊")
            validos = [r for r in resultados if r['url']]
            Logger.sucesso(f"Streams com URL válida: {len(validos)} 🌐")
            Logger.cabecalho("Teste os Streams")
            print(f"  {Estilos.VERDE}🎮 Comando para testar:{Estilos.RESET}")
            url_teste = next((r['url'] for r in resultados if r['url']), "Nenhuma URL disponível")
            print(f"  {Estilos.NEGRITO}ffplay -autoexit {url_teste}{Estilos.RESET}")
            print(f"  {Estilos.NEGRITO}vlc {url_teste}{Estilos.RESET}")
    else:
        Logger.aviso("Nenhum stream processado 😕")

    Logger.cabecalho("Processo Finalizado")

if __name__ == "__main__":
    main()