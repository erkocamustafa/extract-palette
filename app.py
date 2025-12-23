from flask import Flask, render_template, request, jsonify, send_from_directory
from color_engine import process_image
import os
import secrets

app = Flask(__name__)

# --- GÜVENLİK AYARLARI ---
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Blog yazılarını okuyan yardımcı fonksiyon
def get_all_posts():
    posts = []
    if not os.path.exists('posts'):
        os.makedirs('posts')

    files = sorted(os.listdir('posts'))
    
    for filename in files:
        if filename.endswith('.txt'):
            post_id = filename.replace('.txt', '')
            try:
                with open(os.path.join('posts', filename), 'r', encoding='utf-8') as f:
                    title = f.readline().strip()
                    tag = f.readline().strip()
                    gradient = f.readline().strip()
                    
                    posts.append({
                        'id': post_id,
                        'title': title,
                        'tag': tag,
                        'gradient': gradient
                    })
            except Exception as e:
                print(f"Skipping {filename}: {e}")
    return posts

# --- ROTALAR ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inspiration')
def inspiration():
    posts = get_all_posts() 
    return render_template('inspiration.html', posts=posts)

@app.route('/blog/<id>')
def blog_post(id):
    try:
        # GÜVENLİK: Klasör dışına çıkmayı engelle
        if '..' in id or '/' in id:
             return render_template('404.html'), 404

        file_path = os.path.join('posts', f'{id}.txt')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        header_part, body_part = content.split('---', 1)
        lines = header_part.strip().split('\n')
        
        post = {
            "title": lines[0].strip(),
            "tag": lines[1].strip(),
            "gradient": lines[2].strip(),
            "content": body_part.strip(),
            "read_time": "3 min read" 
        }
        return render_template('blog_post.html', post=post)

    except FileNotFoundError:
        return render_template('404.html'), 404
    except Exception as e:
        print(f"Blog Error: {e}")
        return render_template('404.html'), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # GÜVENLİK: Dosya uzantısını kontrol et
    if file and allowed_file(file.filename):
        try:
            result = process_image(file)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload PNG, JPG or WEBP.'}), 400

# 404 Hatası için özel sayfa
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# --- SEO DOSYALARI ---
@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)