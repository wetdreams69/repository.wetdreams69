import os
import glob
import zipfile
import shutil
import xml.etree.ElementTree as ET

def get_version_key(version_str):
    parts = []
    for part in version_str.split('.'):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(part)
    return tuple(parts)

os.makedirs('repo', exist_ok=True)
addon_versions = {}

for zip_path in glob.glob('zips_download/**/*.zip', recursive=True) + glob.glob('zips_download/*.zip'):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            xml_entry = None
            for name in zip_ref.namelist():
                if name.endswith('addon.xml') and not name.startswith('__MACOSX'):
                    xml_entry = name
                    break
            if not xml_entry:
                continue
            xml_content = zip_ref.read(xml_entry)
            root = ET.fromstring(xml_content)
            addon_id = root.attrib['id']
            version = root.attrib['version']
            dest_dir = os.path.join('repo', addon_id)
            os.makedirs(dest_dir, exist_ok=True)
            dest_zip = os.path.join(dest_dir, f"{addon_id}-{version}.zip")
            shutil.copy2(zip_path, dest_zip)
            if addon_id not in addon_versions or get_version_key(version) > get_version_key(addon_versions[addon_id]['version']):
                addon_versions[addon_id] = {
                    'version': version,
                    'xml_content': xml_content
                }
    except Exception as e:
        print(f"Error processing {zip_path}: {e}")

for addon_id, data in addon_versions.items():
    dest_xml = os.path.join('repo', addon_id, 'addon.xml')
    with open(dest_xml, 'wb') as f:
        f.write(data['xml_content'])
