from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'downloads'

# Ensure download directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_video_info(url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info['formats']:
                if f.get('height') in [480, 720, 1080] and f.get('ext') == 'mp4':
                    formats.append({
                        'format_id': f['format_id'],
                        'quality': f'{f["height"]}p',
                        'ext': f['ext']
                    })
            return {
                'title': info['title'],
                'formats': formats,
                'thumbnail': info.get('thumbnail', '')
            }
    except Exception as e:
        return {'error': str(e)}

def download_video(url, format_id):
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], '%(title)s.%(ext)s')
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return os.path.join(app.config['UPLOAD_FOLDER'], f"{info['title']}.{info['ext']}")
    except Exception as e:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'})
    info = get_video_info(url)
    return jsonify(info)

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    format_id = request.json.get('format_id')
    
    if not url or not format_id:
        return jsonify({'error': 'URL and format_id are required'})
    
    file_path = download_video(url, format_id)
    if file_path:
        return jsonify({'success': True, 'file': os.path.basename(file_path)})
    return jsonify({'error': 'Download failed'})

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
