import requests

# URL del post con .json al final
url = "https://www.reddit.com/r/crashbandicoot/comments/j383r0/crash_bandicoot_4_its_about_time_review_thread/.json"
headers = {"User-Agent": "Mozilla/5.0"}

# Descargar el JSON del hilo
response = requests.get(url, headers=headers)
data = response.json()

# Lista para guardar todos los comentarios
todos_los_comentarios = []

# Función recursiva para recorrer comentarios anidados
def extraer_comentarios(comentarios):
    for item in comentarios:
        if item["kind"] == "t1":  # t1 = comentario
            cuerpo = item["data"].get("body")
            if cuerpo:
                todos_los_comentarios.append(cuerpo)

            # Si tiene respuestas (replies), seguir recorriendo
            respuestas = item["data"].get("replies")
            if isinstance(respuestas, dict):
                hijos = respuestas["data"]["children"]
                extraer_comentarios(hijos)

# Extraer la sección de comentarios (segunda parte del JSON)
comentarios_principales = data[1]["data"]["children"]
extraer_comentarios(comentarios_principales)

# Mostrar los primeros 10 comentarios como ejemplo
for i, comentario in enumerate(todos_los_comentarios[:10], 1):
    print(f"Comentario {i}:\n{comentario}\n{'-'*80}")

# Guardar todos los comentarios en un archivo
with open("todos_los_comentarios.txt", "w", encoding="utf-8") as f:
    for comentario in todos_los_comentarios:
        f.write(comentario + "\n\n")