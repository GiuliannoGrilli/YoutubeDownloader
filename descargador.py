import yt_dlp
import argparse
import subprocess
import sys        
import os
from yt_dlp.utils import download_range_func

def tiempo_a_segundos(tiempo_str):
    """Convierte un texto como '1:39' a segundos totales (99)."""
    if not tiempo_str:
        return None
    
    partes = [int(p) for p in tiempo_str.split(':')]
    
    if len(partes) == 2: # Si formato MM:SS
        return partes[0] * 60 + partes[1]
    elif len(partes) == 3: # Si formato largo HH:MM:SS
        return partes[0] * 3600 + partes[1] * 60 + partes[2]
    
    return int(tiempo_str) # Por si solo segundos

def descargar_video(url, resolucion=1080, inicio=None, fin=None, solo_audio=False):
    ruta_destino = os.path.expanduser('~/Downloads/')
    if solo_audio:
        opciones = {
            'format': 'bestaudio/best', # Pista de audio mejor calidad
            'outtmpl': os.path.join(ruta_destino, '%(title)s_audio.%(ext)s'), 
            'postprocessors': [{
                # Le pedimos a FFmpeg que extraiga el audio y lo convierta
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192', # Calidad estándar de MP3
            }],
        }
        print(f"Iniciando descarga de AUDIO: {url} en MP3...")
    else:
        formato_deseado = f'bestvideo[height<={resolucion}]+bestaudio/best[height<={resolucion}]'
    
        opciones = {
            'format': formato_deseado,
            'outtmpl': os.path.join(ruta_destino, f'%(title)s_{resolucion}p.%(ext)s'),
            'merge_output_format': 'mp4', # Forzamos a que el resultado final sea MP4, el estándar más cómodo para editar
        }

    if inicio and fin:
        seg_inicio = tiempo_a_segundos(inicio)
        seg_fin = tiempo_a_segundos(fin)
        # Le indicamos a yt-dlp que descargue solo este rango específico
        opciones['download_ranges'] = download_range_func(None, [(seg_inicio, seg_fin)])
        
        # Forzamos a que FFmpeg haga los cortes precisos y no se desfase el audio
        opciones['force_keyframes_at_cuts'] = True 
        
        print(f"Iniciando descarga: {url}")
        print(f"Resolución: {resolucion}p | Fragmento: {inicio} a {fin}...")
    else:
        print(f"Iniciando descarga de: {url} en {resolucion}p...")
    
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

    # --- AUTOMATIZACIÓN PARA MACOS ---
        if sys.platform == 'darwin':
            print("Ejecutando limpieza de cuarentena de Apple...")
            # subprocess.run es el equivalente a ti escribiendo en la terminal
            subprocess.run(['xattr', '-c', archivo_final], check=False)
            print("¡Archivo liberado y listo para abrirse sin advertencias!")
        
        
    except Exception as e:
        print(f"Ocurrió un error durante la descarga: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descargador de videos de YouTube")
    parser.add_argument("url", type=str, help="El link del video de YouTube")
    parser.add_argument("resolucion", type=int, nargs='?', default=1080, help="La resolución deseada (ej. 480, 720, 1080)")
    
    # --- ARGUMENTOS OPCIONALES PARA RECORTES ---
    parser.add_argument("--inicio", type=str, help="Tiempo de inicio (ej. 0:45)", default=None)
    parser.add_argument("--fin", type=str, help="Tiempo de fin (ej. 1:39)", default=None)

    # Argumento para descargar solamente audio chikistrikis
    parser.add_argument("--audio", action="store_true", help="Descargar solo el audio en MP3")

    args = parser.parse_args()
    descargar_video(args.url, args.resolucion, args.inicio, args.fin, args.audio)