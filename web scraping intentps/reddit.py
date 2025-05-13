import praw
import pandas as pd
import datetime
import argparse
import configparser
import os

def create_reddit_instance(client_id, client_secret, user_agent):
    """
    Crea una instancia de la API de Reddit usando PRAW.
    """
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

def extract_comments(reddit, url):
    """
    Extrae comentarios de un hilo de Reddit específico.
    
    Args:
        reddit: Instancia de la API de Reddit.
        url: URL del hilo de Reddit.
        
    Returns:
        Lista de diccionarios con datos de comentarios.
    """
    # Obtener la publicación de Reddit
    submission = reddit.submission(url=url)
    
    # Expandir todos los comentarios (incluidos los colapsados)
    submission.comments.replace_more(limit=None)
    
    comments_data = []
    
    # Recorrer todos los comentarios
    for comment in submission.comments.list():
        # Convertir el timestamp a fecha legible
        comment_date = datetime.datetime.fromtimestamp(comment.created_utc)
        
        # Crear diccionario con los datos del comentario
        comment_info = {
            'usuario': comment.author.name if comment.author else '[deleted]',
            'fecha': comment_date.strftime('%Y-%m-%d %H:%M:%S'),
            'texto': comment.body,
            'score': comment.score,
            'id': comment.id
        }
        
        comments_data.append(comment_info)
    
    return comments_data

def save_to_csv(comments_data, output_file='reddit_comments.csv'):
    """
    Guarda los comentarios en un archivo CSV.
    """
    df = pd.DataFrame(comments_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Datos guardados en '{output_file}'")
    return df

def setup_config():
    """
    Crea un archivo de configuración para las credenciales de Reddit.
    """
    config = configparser.ConfigParser()
    
    if not os.path.exists('reddit_config.ini'):
        print("Configuración no encontrada. Creando archivo de configuración...")
        
        client_id = input("Ingresa tu Client ID de Reddit: ")
        client_secret = input("Ingresa tu Client Secret de Reddit: ")
        user_agent = input("Ingresa un User Agent (ejemplo: 'comment_scraper by u/YOUR_USERNAME'): ")
        
        config['REDDIT'] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'user_agent': user_agent
        }
        
        with open('reddit_config.ini', 'w') as configfile:
            config.write(configfile)
        
        print("Configuración guardada en 'reddit_config.ini'")
    else:
        config.read('reddit_config.ini')
    
    return config['REDDIT']['client_id'], config['REDDIT']['client_secret'], config['REDDIT']['user_agent']

def main():
    parser = argparse.ArgumentParser(description='Scraper de comentarios de Reddit')
    parser.add_argument('--url', type=str, help='URL del hilo de Reddit', 
                        default="https://www.reddit.com/r/crashbandicoot/comments/j383r0/crash_bandicoot_4_its_about_time_review_thread/")
    parser.add_argument('--output', type=str, help='Nombre del archivo CSV de salida', default='reddit_comments.csv')
    args = parser.parse_args()
    
    # Configurar y obtener credenciales
    client_id, client_secret, user_agent = setup_config()
    
    # Crear instancia de Reddit
    reddit = create_reddit_instance(client_id, client_secret, user_agent)
    
    # Extraer comentarios
    print(f"Extrayendo comentarios de: {args.url}")
    comments_data = extract_comments(reddit, args.url)
    print(f"Se encontraron {len(comments_data)} comentarios")
    
    # Guardar datos
    df = save_to_csv(comments_data, args.output)
    
    # Mostrar una vista previa
    print("\nVista previa de los datos:")
    print(df.head())

if __name__ == "__main__":
    main()