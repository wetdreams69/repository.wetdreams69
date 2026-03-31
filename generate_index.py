import os
import datetime
import math
import sys

def format_size(size):
    if size == 0: return "0 B"
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {['B', 'KB', 'MB', 'GB', 'TB'][i]}"

def generate_index(path, root_path):
    files = os.listdir(path)
    files.sort()
    
    html = """<!DOCTYPE html>
<html>
<head>
<title>Index of /""" + os.path.relpath(path, root_path).replace('.', '') + """</title>
<style>
  body { font-family: monospace; }
  table { border-collapse: collapse; width: 100%; max-width: 800px; }
  th, td { text-align: left; padding: 4px 8px; }
  th { border-bottom: 1px solid #ccc; }
  a { text-decoration: none; color: #0000ee; }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<h1>Index of /""" + os.path.relpath(path, root_path).replace('.', '') + """</h1>
<hr>
<table>
<tr><th>Name</th><th>Last modified</th><th>Size</th></tr>
<tr><td><a href="../">../</a></td><td></td><td></td></tr>
"""

    dirs = [f for f in files if os.path.isdir(os.path.join(path, f))]
    files_only = [f for f in files if os.path.isfile(os.path.join(path, f)) and f != 'index.html']
    
    for d in dirs:
        full_p = os.path.join(path, d)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_p)).strftime('%Y-%m-%d %H:%M')
        html += f'<tr><td><a href="{d}/">{d}/</a></td><td>{mtime}</td><td>-</td></tr>\n'
        generate_index(full_p, root_path)
        
    for f in files_only:
        full_p = os.path.join(path, f)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_p)).strftime('%Y-%m-%d %H:%M')
        size = format_size(os.path.getsize(full_p))
        html += f'<tr><td><a href="{f}">{f}</a></td><td>{mtime}</td><td>{size}</td></tr>\n'
        
    html += """</table>
<hr>
</body>
</html>"""
    
    with open(os.path.join(path, 'index.html'), 'w') as out:
        out.write(html)

if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    generate_index(target_dir, target_dir)
