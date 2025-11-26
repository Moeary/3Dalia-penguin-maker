#!/usr/bin/env python3
"""
Generate meme-manifest.json from meme-base folder
This file is used by the Vue app to load the list of available memes
"""

import os
import json
from pathlib import Path

def generate_manifest():
    # Get the script directory
    script_dir = Path(__file__).parent
    # meme_base_dir is now in public/meme-base
    meme_base_dir = script_dir.parent / 'public' / 'meme-base'
    
    
    # Get all image files
    extensions = {'.webp', '.jpg', '.jpeg', '.png'}
    files = sorted([
        f for f in meme_base_dir.iterdir()
        if f.suffix.lower() in extensions
    ])
    
    # Create manifest
    manifest = [
        {
            'name': f'表情 {i + 1}',
            'path': f'/meme-base/{f.name}',
            'filename': f.name
        }
        for i, f in enumerate(files)
    ]
    
    # Save to public folder for Vite to serve
    public_dir = script_dir / 'public'
    public_dir.mkdir(exist_ok=True)
    
    manifest_path = public_dir / 'meme-manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Generated manifest with {len(manifest)} memes")
    print(f"✓ Saved to {manifest_path}")
    
    return len(manifest)

if __name__ == '__main__':
    generate_manifest()
