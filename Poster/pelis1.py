#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from datetime import datetime, timezone
import time

from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ————————————————————————————————
# 0) Mapeo manual de URLs a nombres de película
# ————————————————————————————————
movie_mapping = {
    "https://www.reddit.com/r/movies/comments/195s51j/eternal_sunshine_of_the_spotless_mind.json": "eternal_sunshine_of_the_spotless_mind",
    "https://www.reddit.com/r/TrueFilm/comments/15gt4gh/mr_nobody_2009.json": "mr_nobody",
    "https://www.reddit.com/r/movies/comments/2ljk71/official_discussion_interstellar_wide_release.json": "interestelar",
    "https://www.reddit.com/r/movies/comments/17cu9sr/moon_2009_is_the_worst_movie_i_have_ever_watched.json": "moon",
    "https://www.reddit.com/r/movies/comments/132zxlu/ex_machina_is_a_wonderful_movie_with_amazing.json": "ex_machina",
    "https://www.reddit.com/r/netflix/comments/1b0ibe9/is_love_death_robots_is_worth_watching.json": "love_death_robots",
    "https://www.reddit.com/r/movies/comments/ol7bn1/many_people_missed_the_point_of_500_days_of.json": "500_days_with_summer",
    "https://www.reddit.com/r/moviecritic/comments/1hrx15y/her_2013_was_set_in_2025_drop_your_thoughts_about.json": "her"
}

# ————————————————————————————————
# 1) Scraping de comentarios de Reddit
# ————————————————————————————————
urls = list(movie_mapping.keys())
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
}
comentarios = []

def extraer_comentarios(lista, nivel, base, titulo):
    if not lista:
        return
    for item in lista:
        if item.get("kind") == "t1":
            d = item["data"]
            texto = d.get("body", "")
            if texto and texto not in ("[deleted]", "[removed]"):
                comentarios.append({
                    "Movie": titulo,
                    "URL": base.replace(".json", ""),
                    "Fecha UTC": datetime.fromtimestamp(
                        d.get("created_utc", 0), tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S'),
                    "Autor": d.get("author", "[deleted]"),
                    "Comentario": texto,
                    "Puntaje": d.get("score", 0),
                    "Nivel": nivel
                })
            rep = d.get("replies")
            if isinstance(rep, dict):
                hijos = rep.get("data", {}).get("children", [])
                extraer_comentarios(hijos, nivel + 1, base, titulo)

for i, url in enumerate(urls):
    if i > 0:
        time.sleep(2)
    try:
        r = requests.get(url, headers=headers, params={'raw_json': 1}, timeout=30)
        r.raise_for_status()
        data = r.json()
        titulo = movie_mapping[url]
        extraer_comentarios(data[1]["data"]["children"], 1, url, titulo)
        print(f"Procesado {i+1}/{len(urls)} → {len(comentarios)} comentarios")
    except Exception as e:
        print(f"Error en URL {i+1}: {e}")

# ————————————————————————————————
# 2) DataFrame base y nuevas columnas
# ————————————————————————————————
DF_COLUMNS = ['Movie', 'URL', 'Fecha UTC', 'Autor', 'Comentario', 'Puntaje', 'Nivel']
df = pd.DataFrame(comentarios, columns=DF_COLUMNS)
df['NumChars'] = df['Comentario'].apply(len)
df['NumWords'] = df['Comentario'].apply(lambda x: len(x.split()))
df['Polarity'] = df['Comentario'].apply(lambda x: TextBlob(x).sentiment.polarity)
df['Subjectivity'] = df['Comentario'].apply(lambda x: TextBlob(x).sentiment.subjectivity)

# ————————————————————————————————
# 3) EDA Gráficos Univariados
# ————————————————————————————————
for col in ['NumChars', 'NumWords', 'Polarity', 'Puntaje']:
    plt.figure()
    plt.boxplot(df[col].dropna(), vert=True)
    plt.title(f"Boxplot de {col}")
    plt.ylabel(col)
    plt.tight_layout()
    plt.show()

# Conteo de comentarios por película
tf = df['Movie'].value_counts()
plt.figure()
plt.bar(tf.index, tf.values)
plt.xticks(rotation=45, ha='right')
plt.title("Comentarios por Película")
plt.tight_layout()
plt.show()

# ————————————————————————————————
# 4) Clustering: Escalado → Elbow → KMeans → Visualización
# ————————————————————————————————
# 4.1) Selección de columnas numéricas
tab_clust = ['NumChars', 'NumWords', 'Polarity', 'Subjectivity', 'Puntaje']
X = df[tab_clust].values

# 4.2) Escalado de características
scaler = StandardScaler()
scaled = scaler.fit_transform(X)

# 4.3) Elbow Method
inertia = []
K_range = range(1, 11)
for k in K_range:
    km_tmp = KMeans(n_clusters=k, init='k-means++', random_state=42)
    km_tmp.fit(scaled)
    inertia.append(km_tmp.inertia_)

plt.figure()
plt.plot(K_range, inertia, 'bx-')
plt.xlabel('Número de clusters k')
plt.ylabel('Inercia')
plt.title('Método del codo (Elbow Method)')
plt.tight_layout()
plt.show()

# 4.4) Entrenar KMeans con k óptimo
k_opt = 3  # Ajustar según elbow
kmeans = KMeans(n_clusters=k_opt, init='k-means++', random_state=42)
kmeans.fit(scaled)

# 4.5) Añadir etiquetas al DataFrame
df['Cluster'] = kmeans.labels_

# 4.6) Pairplot coloreado por cluster
sns.pairplot(
    df,
    vars=tab_clust,
    hue='Cluster',
    palette='Set2',
    diag_kind='kde'
)
plt.show()

# 4.7) Scatter NumWords vs Polarity con centroides desescalados
f1 = df['NumWords']
f2 = df['Polarity']
plt.figure(figsize=(8, 6))
for lbl in range(k_opt):
    mask = df['Cluster'] == lbl
    plt.scatter(f1[mask], f2[mask], label=f'Cluster {lbl}', s=50, alpha=0.6)

centros_escalados = kmeans.cluster_centers_
centros_orig = scaler.inverse_transform(centros_escalados)
i_f1 = tab_clust.index('NumWords')
i_f2 = tab_clust.index('Polarity')
plt.scatter(
    centros_orig[:, i_f1],
    centros_orig[:, i_f2],
    marker='*', c='black', s=200, label='Centroides'
)
plt.xlabel('NumWords')
plt.ylabel('Polarity')
plt.legend()
plt.title('Clusters sobre NumWords vs Polarity')
plt.tight_layout()
plt.show()

sns.boxplot(data=df)
plt.show()