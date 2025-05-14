import requests
import pandas as pd
from datetime import datetime, timezone

# --- Lista de URLs de Reddit en formato .json ---
urls = [
    "https://www.reddit.com/r/crashbandicoot/comments/j383r0/crash_bandicoot_4_its_about_time_review_thread/.json",
    "https://www.reddit.com/r/Games/comments/11tjv4i/resident_evil_4_2023_remake_review_thread/.json",
    "https://www.reddit.com/r/patientgamers/comments/rjf9mz/alan_wake_is_a_masterpiece/.json",
    "https://www.reddit.com/r/Games/comments/1lq0ld/outlast_review_thread/.json",
    #"https://www.reddit.com/r/Games/comments/1fvt8b9/silent_hill_2_review_thread/#:~:text=Faithful%20and%20very%20different%2C%20this,great%20hope%20for%20the%20future."  # <- Agrega más si deseas
]

headers = {"User-Agent": "Mozilla/5.0"}
comentarios = []

# --- Función recursiva para extraer comentarios ---
def extraer_comentarios(lista_comentarios, nivel, url_base):
    for item in lista_comentarios:
        if item["kind"] == "t1":
            datos = item["data"]
            cuerpo = datos.get("body", "")
            autor = datos.get("author", "[deleted]")
            timestamp = datos.get("created_utc", 0)
            fecha = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            score = datos.get("score", 0)
            id_comentario = datos.get("id", "")
            permalink = f"https://www.reddit.com{datos.get('permalink', '')}"

            comentarios.append({
                "Post URL": url_base.replace(".json", ""),
                "Fecha UTC": fecha,
                "Autor": autor,
                "Comentario": cuerpo,
                "Puntaje": score,
                "Nivel (anidamiento)": nivel,
                "ID Comentario": id_comentario,
                "Enlace Comentario": permalink
            })

            respuestas = datos.get("replies")
            if isinstance(respuestas, dict):
                hijos = respuestas["data"]["children"]
                extraer_comentarios(hijos, nivel+1, url_base)

# --- Procesar cada URL ---
for url in urls:
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        comentarios_principales = data[1]["data"]["children"]
        extraer_comentarios(comentarios_principales, nivel=1, url_base=url)
        print(f"✅ Procesado: {url}")
    except Exception as e:
        print(f"❌ Error con {url}: {e}")

# --- Exportar todo a un solo Excel ---
df = pd.DataFrame(comentarios)
ruta_salida = r"C:/Users/aaram/Documents/5to semestre/DIplomado datos/reddit/reddit_comentarios_consolidados2.xlsx"
df.to_excel(ruta_salida, index=False)
print(f"✅ Archivo consolidado guardado en: {ruta_salida}")

