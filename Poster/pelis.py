
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from datetime import datetime, timezone
import time

# --- Lista de URLs de Reddit en formato .json ---
urls = [
    "https://www.reddit.com/r/movies/comments/195s51j/eternal_sunshine_of_the_spotless_mind.json",
    "https://www.reddit.com/r/TrueFilm/comments/15gt4gh/mr_nobody_2009.json",
    "https://www.reddit.com/r/movies/comments/2ljk71/official_discussion_interstellar_wide_release.json",
    "https://www.reddit.com/r/movies/comments/17cu9sr/moon_2009_is_the_worst_movie_i_have_ever_watched/.json",
    "https://www.reddit.com/r/movies/comments/hqum3m/what_do_you_think_about_the_babadook_2014/.json",
    "https://www.reddit.com/r/movies/comments/132zxlu/ex_machina_is_a_wonderful_movie_with_amazing/.json",
    "https://www.reddit.com/r/netflix/comments/1b0ibe9/is_love_death_robots_is_worth_watching/.json",
    "https://www.reddit.com/r/movies/comments/ol7bn1/many_people_missed_the_point_of_500_days_of/.json",
    "https://www.reddit.com/r/moviecritic/comments/1hrx15y/her_2013_was_set_in_2025_drop_your_thoughts_about/.json",
]

# Headers más completos para evitar bloqueos
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

comentarios = []

# --- Función recursiva para extraer comentarios ---
def extraer_comentarios(lista_comentarios, nivel, url_base, post_title=""):
    if not lista_comentarios:
        return
        
    for item in lista_comentarios:
        if item["kind"] == "t1":  # Comentario
            datos = item["data"]
            cuerpo = datos.get("body", "")
            autor = datos.get("author", "[deleted]")
            timestamp = datos.get("created_utc", 0)
            
            # Convertir timestamp a fecha legible
            if timestamp:
                fecha = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            else:
                fecha = "N/A"
            
            score = datos.get("score", 0)
            id_comentario = datos.get("id", "")
            permalink = f"https://www.reddit.com{datos.get('permalink', '')}"
            
            # Filtrar comentarios eliminados o vacíos
            if cuerpo and cuerpo not in ["[deleted]", "[removed]", ""]:
                comentarios.append({
                    "Post Title": post_title,
                    "Post URL": url_base.replace(".json", ""),
                    "Fecha UTC": fecha,
                    "Autor": autor,
                    "Comentario": cuerpo,
                    "Puntaje": score,
                    "Nivel (anidamiento)": nivel,
                    "ID Comentario": id_comentario,
                    "Enlace Comentario": permalink
                })
            
            # Procesar respuestas (comentarios anidados)
            respuestas = datos.get("replies")
            if isinstance(respuestas, dict) and "data" in respuestas:
                hijos = respuestas["data"]["children"]
                extraer_comentarios(hijos, nivel + 1, url_base, post_title)

# --- Procesar cada URL ---
for i, url in enumerate(urls):
    try:
        print(f"Procesando URL {i+1}/{len(urls)}: {url}")
        
        # Agregar pausa entre requests para evitar rate limiting
        if i > 0:
            time.sleep(2)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Levanta excepción si hay error HTTP
        
        data = response.json()
        
        # Extraer título del post
        post_title = ""
        if len(data) > 0 and "data" in data[0] and "children" in data[0]["data"]:
            post_data = data[0]["data"]["children"][0]["data"]
            post_title = post_data.get("title", "Sin título")
        
        # Extraer comentarios (están en data[1])
        if len(data) > 1 and "data" in data[1]:
            comentarios_principales = data[1]["data"]["children"]
            extraer_comentarios(comentarios_principales, nivel=1, url_base=url, post_title=post_title)
            print(f"✅ Procesado: {url} - Comentarios encontrados hasta ahora: {len(comentarios)}")
        else:
            print(f"⚠️ No se encontraron comentarios en: {url}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión con {url}: {e}")
    except ValueError as e:
        print(f"❌ Error al parsear JSON de {url}: {e}")
    except Exception as e:
        print(f"❌ Error inesperado con {url}: {e}")

# --- Verificar si se extrajeron comentarios ---
if comentarios:
    # --- Exportar todo a un solo Excel ---
    df = pd.DataFrame(comentarios)
    ruta_salida = r"C:/Users/aaram/Documents/5to semestre/DIplomado datos/Actividad 3/Comentarios_Reddit.xlsx"
    
    try:
        df.to_excel(ruta_salida, index=False)
        print(f"✅ Archivo consolidado guardado en: {ruta_salida}")
        print(f"📊 Total de comentarios extraídos: {len(comentarios)}")
        
        # Mostrar estadísticas básicas
        print("\n📈 Estadísticas:")
        print(f"- Comentarios por nivel de anidamiento:")
        print(df['Nivel (anidamiento)'].value_counts().sort_index())
        print(f"- Comentarios por post:")
        print(df['Post Title'].value_counts())
        
    except Exception as e:
        print(f"❌ Error al guardar el archivo Excel: {e}")
        # Como alternativa, guardar como CSV
        ruta_csv = ruta_salida.replace('.xlsx', '.csv')
        df.to_csv(ruta_csv, index=False, encoding='utf-8')
        print(f"✅ Guardado como CSV en: {ruta_csv}")
else:
    print("❌ No se extrajeron comentarios. Verifica las URLs y la conectividad.")

print("\n🔍 Script completado.")   


