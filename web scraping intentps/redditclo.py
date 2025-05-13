import requests
import re
import json
import pandas as pd
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
import time
import random

def get_user_agent():
    """
    Genera un user agent aleatorio para evitar ser bloqueado.
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    ]
    return random.choice(user_agents)

def extract_comments_from_html(url):
    """
    Extrae los comentarios directamente del HTML de Reddit.
    """
    # Modificar la URL para obtener la versión JSON (.json)
    if not url.endswith('/'):
        url += '/'
    
    json_url = url + '.json'
    
    headers = {
        'User-Agent': get_user_agent(),
        'Accept': 'application/json'
    }
    
    # Hacer la solicitud HTTP
    print(f"Accediendo a {json_url}")
    response = requests.get(json_url, headers=headers)
    
    # Verificar si la solicitud fue exitosa
    if response.status_code != 200:
        print(f"Error al acceder a Reddit. Código de estado: {response.status_code}")
        return []
    
    # Cargar los datos JSON
    data = response.json()
    
    # Lista para almacenar los comentarios
    comments_data = []
    
    # Procesar los comentarios del primer nivel
    if len(data) > 1 and 'data' in data[1] and 'children' in data[1]['data']:
        for child in data[1]['data']['children']:
            if child['kind'] == 't1':  # 't1' es el tipo para comentarios
                comment = child['data']
                
                # Convertir el timestamp a fecha legible
                comment_date = datetime.fromtimestamp(comment['created_utc'])
                
                # Añadir el comentario a la lista
                comments_data.append({
                    'usuario': comment.get('author', '[deleted]'),
                    'fecha': comment_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'texto': comment.get('body', ''),
                    'score': comment.get('score', 0),
                    'id': comment.get('id', '')
                })
                
                # Procesar respuestas a este comentario si existen
                if 'replies' in comment and comment['replies'] != '':
                    if isinstance(comment['replies'], dict) and 'data' in comment['replies']:
                        extract_replies(comment['replies']['data']['children'], comments_data)
    
    return comments_data

def extract_replies(replies, comments_data):
    """
    Extrae las respuestas a los comentarios de forma recursiva.
    """
    for reply in replies:
        if reply['kind'] == 't1':  # 't1' es el tipo para comentarios
            comment = reply['data']
            
            # Convertir el timestamp a fecha legible
            comment_date = datetime.fromtimestamp(comment['created_utc'])
            
            # Añadir el comentario a la lista
            comments_data.append({
                'usuario': comment.get('author', '[deleted]'),
                'fecha': comment_date.strftime('%Y-%m-%d %H:%M:%S'),
                'texto': comment.get('body', ''),
                'score': comment.get('score', 0),
                'id': comment.get('id', '')
            })
            
            # Procesar respuestas a este comentario si existen
            if 'replies' in comment and comment['replies'] != '':
                if isinstance(comment['replies'], dict) and 'data' in comment['replies']:
                    extract_replies(comment['replies']['data']['children'], comments_data)

def save_to_csv(comments_data, output_file='reddit_comments.csv'):
    """
    Guarda los comentarios en un archivo CSV.
    """
    df = pd.DataFrame(comments_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Datos guardados en '{output_file}'")
    return df

def main():
    parser = argparse.ArgumentParser(description='Scraper de comentarios de Reddit sin autenticación')
    parser.add_argument('--url', type=str, help='URL del hilo de Reddit', 
                       default="https://www.reddit.com/r/crashbandicoot/comments/j383r0/crash_bandicoot_4_its_about_time_review_thread/")
    parser.add_argument('--output', type=str, help='Nombre del archivo CSV de salida', default='reddit_comments.csv')
    args = parser.parse_args()
    
    # Extraer comentarios
    print(f"Extrayendo comentarios de: {args.url}")
    comments_data = extract_comments_from_html(args.url)
    print(f"Se encontraron {len(comments_data)} comentarios")
    
    # Guardar datos
    if comments_data:
        df = save_to_csv(comments_data, args.output)
        
        # Mostrar una vista previa
        print("\nVista previa de los datos:")
        print(df.head())
    else:
        print("No se encontraron comentarios.")

if __name__ == "__main__":
    main()