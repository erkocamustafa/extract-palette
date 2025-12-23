import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import math

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def get_average_color(image):
    avg_color_per_row = np.average(image, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    return rgb_to_hex(avg_color)

def calculate_color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def get_smart_usage(width, height, dominant_colors_rgb):
    sat_scores = []
    bright_scores = []
    
    for color in dominant_colors_rgb[:3]: 
        r, g, b = color
        mx, mn = max(r, g, b), min(r, g, b)
        s = 0 if mx == 0 else ((mx - mn) / mx) * 100
        v = (mx / 255) * 100
        sat_scores.append(s)
        bright_scores.append(v)
        
    avg_sat = sum(sat_scores) / len(sat_scores) if sat_scores else 0
    avg_bright = sum(bright_scores) / len(bright_scores) if bright_scores else 0
    
    if avg_bright < 40: vibe = "Moody"
    elif avg_sat > 50: vibe = "Vibrant" 
    elif avg_sat < 10: vibe = "Minimal"
    else: vibe = "Balanced"
    
    ratio = width / height
    
    if 0.8 <= ratio <= 1.2: 
        if vibe == "Vibrant": return "Product Ad / Promo 🛍️"
        if vibe == "Moody": return "Album Cover / Art 🎨"
        return "Instagram Post 🟦"
    elif ratio < 0.8: 
        if vibe == "Vibrant": return "Viral Reels / TikTok ⚡"
        if vibe == "Moody": return "Wallpaper / Lockscreen 🔒"
        return "Instagram Story 📸"
    elif ratio > 1.2: 
        if vibe == "Minimal": return "Website Hero / Header 💻"
        return "YouTube Thumbnail 📺"
        
    return "General Usage 🖼️"

def process_image(image_stream, k=5):
    file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    h_orig, w_orig = image.shape[:2]

    if w_orig > 600:
        new_h = int(h_orig * (600 / w_orig))
        process_img = cv2.resize(image, (600, new_h), interpolation=cv2.INTER_AREA)
    else:
        process_img = image

    search_k = 10 
    image_reshaped = process_img.reshape((process_img.shape[0] * process_img.shape[1], 3))
    
    clt = KMeans(n_clusters=search_k, n_init=10)
    clt.fit(image_reshaped)
    
    # --- YENİ EKLENEN KISIM: Yüzde Hesabı ---
    labels = clt.labels_
    label_counts = Counter(labels)
    total_pixels = sum(label_counts.values())
    
    candidates = clt.cluster_centers_
    
    scored_candidates = []
    for i, color in enumerate(candidates):
        r, g, b = color
        mx, mn = max(r, g, b), min(r, g, b)
        s = 0 if mx == 0 else ((mx - mn) / mx) * 100
        v = (mx / 255) * 100
        score = (s * 2.5) + (v * 1.0) 
        if s < 5 and 20 < v < 90: score -= 20 
        
        percent = (label_counts[i] / total_pixels) * 100
        
        scored_candidates.append({
            'score': score,
            'color': color,
            'percent': percent
        })
    
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    final_colors_data = []
    for candidate_data in scored_candidates:
        if len(final_colors_data) >= k: break
        candidate_color = candidate_data['color']
        is_distinct = True
        for selected in final_colors_data:
            if calculate_color_distance(candidate_color, selected['color']) < 35:
                is_distinct = False
                break
        if is_distinct: final_colors_data.append(candidate_data)
            
    if len(final_colors_data) < k:
        for candidate_data in scored_candidates:
            if len(final_colors_data) >= k: break
            candidate_color = candidate_data['color']
            is_distinct = True
            for selected in final_colors_data:
                 if calculate_color_distance(candidate_color, selected['color']) < 10: is_distinct = False
            if is_distinct: final_colors_data.append(candidate_data)

    hex_colors = [rgb_to_hex(c['color']) for c in final_colors_data]
    percentages = [round(c['percent'], 1) for c in final_colors_data]
    
    avg_hex = get_average_color(process_img)
    usage = get_smart_usage(w_orig, h_orig, [c['color'] for c in final_colors_data]) 
    
    avg_rgb = hex_to_rgb(avg_hex)
    luminance = (0.299*avg_rgb[0] + 0.587*avg_rgb[1] + 0.114*avg_rgb[2])
    contrast_text = "White Text" if luminance < 128 else "Black Text"

    return {
        "colors": hex_colors,
        "percentages": percentages,
        "average": avg_hex,
        "usage": usage,
        "contrast": contrast_text
    }