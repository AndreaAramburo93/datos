#esta funcina, y trae los comentarios 

import requests

# 1. URL del post en formato .json
url = "https://www.reddit.com/r/crashbandicoot/comments/j383r0/crash_bandicoot_4_its_about_time_review_thread/.json"

# 2. Headers para evitar el bloqueo por parte de Reddit
headers = {'User-agent': 'Mozilla/5.0'}

# 3. Petición
response = requests.get(url, headers=headers)
data = response.json()

# 4. Acceso a comentarios
comentarios_raw = data[1]["data"]["children"]

# 5. Extraer texto de los comentarios
comentarios = []
for item in comentarios_raw:
    if item["kind"] == "t1":
        comentario = item["data"]["body"]
        comentarios.append(comentario)

# 6. Mostrar los primeros 5 comentarios
for i, c in enumerate(comentarios[:20], 1):
    print(f"Comentario {i}:\n{c}\n{'-'*80}")

# Opcional: guardar en archivo
with open("comentarios_reddit.txt", "w", encoding="utf-8") as f:
    for c in comentarios:
        f.write(c + "\n\n")