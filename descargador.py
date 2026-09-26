import yt_dlp
import argparse
import subprocess
import sys        
import os
from typing import Any
from yt_dlp import download_range_func


def notificar_mac(mensaje, titulo="SpotDark"):
    """Envía una notificación nativa en macOS."""
    if sys.platform == 'darwin':
        script = f'display notification "{mensaje}" with title "{titulo}"'
        subprocess.run(['osascript', '-e', script], check=False)

def tiempo_a_segundos(tiempo_str):
    if not tiempo_str:
        return None
    partes = [int(p) for p in tiempo_str.split(':')]
    if len(partes) == 2:
        return partes[0] * 60 + partes[1]
    elif len(partes) == 3:
        return partes[0] * 3600 + partes[1] * 60 + partes[2]
    return int(tiempo_str)

def obtener_formatos_video(url: str) -> list[int]:
    """Obtiene una lista de las resoluciones de video disponibles (heights)."""
    navegador_para_cookies = ('firefox',)
    opciones: dict[str, Any] = {
        'cookiesfrombrowser': navegador_para_cookies,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl: # type: ignore
            info = ydl.extract_info(url, download=False)
            if not info: return []
            formatos = info.get('formats', [])
            
            resoluciones = set()
            for f in formatos:
                if f.get('vcodec') != 'none' and f.get('height'):
                    resoluciones.add(f.get('height'))
                    
            return sorted(list(resoluciones))
    except Exception as e:
        print(f"Error al obtener formatos: {e}")
        return []

def descargar_video(url, resolucion=1080, inicio=None, fin=None, solo_audio=False):
    ruta_destino = os.path.expanduser('~/Desktop/')
    
    notificar_mac(f"Iniciando descarga...", "SpotDark")
    
    navegador_para_cookies = ('firefox',)
    opciones: dict[str, Any] = {
        'cookiesfrombrowser': navegador_para_cookies,
        'remote_components': ['ejs:github'],
        'noplaylist': True,
    }

    if solo_audio:
        opciones.update({
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(ruta_destino, '%(title)s_audio.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
        print(f"Iniciando descarga de AUDIO: {url} en MP3...")
    else:
        # height<={resolucion} hace que yt-dlp elija automaticamente la mejor
        # resolucion disponible <= la pedida (fallback automatico).
        formato_deseado = (
            f'bestvideo[height<={resolucion}]+bestaudio/'
            f'bestvideo[height<={resolucion}]+bestaudio[ext=m4a]/'
            f'best[height<={resolucion}]'
        )
        opciones.update({
            'format': formato_deseado,
            # %(height)s en el nombre refleja la resolucion REAL descargada
            'outtmpl': os.path.join(ruta_destino, '%(title)s_%(height)sp.%(ext)s'),
            'merge_output_format': 'mp4',
        })

    if inicio and fin:
        seg_inicio = tiempo_a_segundos(inicio)
        seg_fin = tiempo_a_segundos(fin)
        if seg_inicio is not None and seg_fin is not None:
            opciones['download_ranges'] = download_range_func(None, [(int(seg_inicio), int(seg_fin))])
        opciones['force_keyframes_at_cuts'] = True
        print(f"Resolución solicitada: {resolucion}p | Fragmento: {inicio} a {fin}...")
    else:
        print(f"Iniciando descarga de: {url} | Resolución solicitada: {resolucion}p (se usará la más cercana disponible)...")
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl: 
            info = ydl.extract_info(url, download=True)
            if 'requested_downloads' in info:
                archivo_final = info['requested_downloads'][0]['filepath']
            else:
                archivo_final = ydl.prepare_filename(info)
                base, _ = os.path.splitext(archivo_final)
                archivo_final = f"{base}.mp3" if solo_audio else f"{base}.mp4"
        
        print("¡Descarga completada con éxito!")

        if sys.platform == 'darwin':
            print("Ejecutando limpieza de cuarentena...")
            subprocess.run(['xattr', '-c', archivo_final], check=False)
            
            nombre_corto = os.path.basename(archivo_final)
            notificar_mac(f"¡Listo! {nombre_corto} guardado en Descargas.", "SpotDark")
        
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        notificar_mac(f"Error al descargar: revisa el link o tu conexión.", "SpotDark - Error")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descargador de videos de YouTube")
    parser.add_argument("url", type=str, help="El link del video de YouTube")
    parser.add_argument("resolucion", type=int, nargs='?', default=1080, help="La resolución deseada (ej. 480, 720, 1080)")
    parser.add_argument("--inicio", type=str, help="Tiempo de inicio (ej. 0:45)", default=None)
    parser.add_argument("--fin", type=str, help="Tiempo de fin (ej. 1:39)", default=None)
    parser.add_argument("--audio", action="store_true", help="Descargar solo el audio en MP3")

    args = parser.parse_args()
    descargar_video(args.url, args.resolucion, args.inicio, args.fin, args.audio)