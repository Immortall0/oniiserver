from flask import Flask, send_from_directory, abort, redirect, request, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'x7k9pL2mN8qR4tV6wY1zA3cE5fG8hJ0kM2nP4rT6vX8yZ'  


DIRECTORY = r'./oniiserverfolder' 


HIDDEN_FILES = {
    'serverupload.py',
    '.gitignore',
}


app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024


ALLOWED_EXTENSIONS = None

@app.route('/', defaults={'req_path': ''}, methods=['GET', 'POST'])
@app.route('/<path:req_path>', methods=['GET', 'POST'])
def serve(req_path):
    abs_path = os.path.abspath(os.path.join(DIRECTORY, req_path))

    
    if not abs_path.startswith(os.path.abspath(DIRECTORY)):
        abort(404)

    if not os.path.exists(abs_path):
        abort(404)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file was selected.', 'error')
            return redirect(request.url)

        files = request.files.getlist('file')  
        uploaded = 0
        for file in files:
            if file.filename == '':
                continue 

            
            filename = os.path.basename(file.filename)
            file_path = os.path.join(abs_path, filename)

            
            counter = 1
            original_name = filename
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_name)
                filename = f"{name} ({counter}){ext}"
                file_path = os.path.join(abs_path, filename)
                counter += 1

            file.save(file_path)
            uploaded += 1

        if uploaded > 0:
            flash(f'{uploaded} File uploaded!', 'success')
        else:
            flash('No file to upload.', 'error')

        return redirect(request.url)

    
    if os.path.isfile(abs_path):
        filename = os.path.basename(abs_path)
        if filename in HIDDEN_FILES:
            abort(404)
        return send_from_directory(DIRECTORY, req_path)

    if os.path.isdir(abs_path):
        if req_path and not req_path.endswith('/'):
            return redirect(request.path + '/')

        
        all_entries = os.listdir(abs_path)
        all_entries.sort(key=lambda x: (not os.path.isdir(os.path.join(abs_path, x)), x.lower()))
        entries = [e for e in all_entries if e not in HIDDEN_FILES]

        
        if req_path:
            display_path = '/' + req_path.rstrip('/') + '/'
        else:
            display_path = '/'

        
        html = '''
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Directory Listing: %(display_path)s</title>
            <style>
                :root { --bg: #f8f9fa; --text: #212529; --link: #0d6efd; --hover: #0b5ed7; --border: #dee2e6; --success: #d4edda; --error: #f8d7da; }
                @media (prefers-color-scheme: dark) {
                    :root { --bg: #212529; --text: #f8f9fa; --link: #0d6efd; --hover: #409cff; --border: #495057; --success: #155724; --error: #721c24; }
                }
                body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; line-height: 1.6; }
                .container { max-width: 960px; margin: 0 auto; }
                h1 { font-size: 1.8rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
                ul { list-style: none; padding: 0; margin: 20px 0; }
                li { padding: 12px 0; border-bottom: 1px solid var(--border); }
                li:last-child { border-bottom: none; }
                a { color: var(--link); text-decoration: none; font-size: 1.1rem; display: flex; align-items: center; }
                a:hover { color: var(--hover); }
                .icon { margin-right: 12px; font-size: 1.4rem; width: 30px; text-align: center; }
                .parent { font-weight: bold; color: #6c757d; }
                .upload-form { background: rgba(0,0,0,0.05); padding: 20px; border-radius: 8px; margin: 20px 0; }
                .upload-form input[type="file"] { margin: 10px 0; }
                .upload-form button { background: #0d6efd; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 1rem; }
                .upload-form button:hover { background: #0b5ed7; }
                .message { padding: 12px; margin: 15px 0; border-radius: 4px; }
                .success { background: var(--success); color: #155724; }
                .error { background: var(--error); color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 %(display_path)s</h1>

                <!-- Message success/error -->
                %(flash_messages)s

                <!-- Form Upload -->
                <div class="upload-form">
                    <h3>📤 Upload file in this folder</h3>
                    <form method="post" enctype="multipart/form-data">
                        <input type="file" name="file" multiple required>
                        <br>
                        <button type="submit">Submit</button>
                    </form>
                    <small>MAX 100MB per File</small>
                </div>

                <ul>
        '''

        
        flash_messages = ''
        for category, message in [('success', 'success'), ('error', 'error')]:
            if flash_msg := flash(category):
                for msg in flash_msg:
                    flash_messages += f'<div class="message {category}">{msg}</

        
        if req_path:
            cleaned_path = req_path.rstrip('/')
            parent = os.path.dirname(cleaned_path)
            parent_link = '/' if not parent or parent == '.' else '/' + parent + '/'
            html += '''
                    <li><a href="%(parent_link)s" class="parent"><span class="icon">🔙</span> .. (Parent Directory)</a></li>
            ''' % {'parent_link': parent_link}

        
        for entry in entries:
            entry_path = os.path.join(req_path, entry).replace('\\', '/')
            full_entry = os.path.join(abs_path, entry)
            icon = '📁' if os.path.isdir(full_entry) else '📄'
            link_end = '/' if os.path.isdir(full_entry) else ''
            html += '''
                    <li><a href="/%(entry_path)s%(link_end)s"><span class="icon">%(icon)s</span> %(entry)s%(slash)s</a></li>
            ''' % {'entry_path': entry_path, 'link_end': link_end, 'icon': icon, 'entry': entry, 'slash': '/' if os.path.isdir(full_entry) else ''}

        html += '''
                </ul>
            </div>
        </body>
        </html>
        '''

        return html % {'display_path': display_path, 'flash_messages': flash_messages}

    abort(404)


if __name__ == "__main__":
    print("Server is running on: http://localhost:9000")
    print(f"Folder: {DIRECTORY}")
    print("Ctrl+C To stop")
    app.run(host="0.0.0.0", port=9000, debug=False)