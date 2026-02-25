import os
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import cv2
import numpy as np
from ultralytics import YOLO
from .models import DetectionResult, SearchHistory

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

try:
    model = YOLO("yolov8n.pt")
except Exception:
    model = None


def index(request):
    return render(request, 'detector_app/index.html')


# ── PROXY DE IMÁGENES ─────────────────────────────────────────────────────────
def proxy_image(request, article):
    """
    Proxy: el server Django busca la imagen en Wikipedia y la devuelve al browser.
    Así no hay bloqueos de hotlink ni CORS — el browser solo habla con Django.
    """
    try:
        headers = {'User-Agent': 'SpeciesDetector/1.0 (educational project)'}
        # 1. Obtener URL de imagen desde Wikipedia
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(article)}"
        r = requests.get(api_url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            img_url = ''
            if data.get('originalimage'):
                img_url = data['originalimage'].get('source', '')
            elif data.get('thumbnail'):
                img_url = data['thumbnail'].get('source', '')

            if img_url:
                # 2. Descargar la imagen y servir al browser
                img_r = requests.get(img_url, headers=headers, timeout=12)
                if img_r.status_code == 200:
                    content_type = img_r.headers.get('Content-Type', 'image/jpeg')
                    response = HttpResponse(img_r.content, content_type=content_type)
                    response['Cache-Control'] = 'public, max-age=86400'  # cache 1 día
                    return response
    except Exception as e:
        pass

    # Fallback: placeholder verde con el nombre
    return HttpResponseRedirect(
        f'https://placehold.co/400x300/061209/4ade80?text={article.replace("_", "+")}'
    )


# ── WIKIPEDIA ─────────────────────────────────────────────────────────────────
def search_wikipedia(query, lang='en'):
    wiki_lang = 'es' if lang == 'es' else 'en'
    headers = {'User-Agent': 'SpeciesDetector/1.0'}

    def fetch_summary(title):
        try:
            r = requests.get(
                f"https://{wiki_lang}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}",
                headers=headers, timeout=8
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    'extract': d.get('extract', '')[:2000],
                    'image': d.get('originalimage', {}).get('source') or d.get('thumbnail', {}).get('source', ''),
                    'url': d.get('content_urls', {}).get('desktop', {}).get('page', ''),
                }
        except Exception:
            pass
        return None

    result = fetch_summary(query)
    if result and result['extract']:
        return result

    try:
        sr = requests.get(
            f"https://{wiki_lang}.wikipedia.org/w/api.php",
            params={'action': 'query', 'list': 'search', 'srsearch': query,
                    'format': 'json', 'srlimit': 3},
            headers=headers, timeout=8
        )
        for hit in sr.json().get('query', {}).get('search', []):
            r = fetch_summary(hit['title'])
            if r and r['extract']:
                return r
    except Exception:
        pass
    return None


# ── GEMINI ────────────────────────────────────────────────────────────────────
def call_gemini(prompt):
    if not GEMINI_API_KEY:
        return None, 'Gemini API key not configured'
    try:
        res = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.1, "maxOutputTokens": 700}},
            timeout=20,
        )
        if res.status_code != 200:
            return None, f"Gemini error {res.status_code}"

        text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        if '```' in text:
            for part in text.split('```'):
                part = part.strip().lstrip('json').strip()
                if part.startswith('{'):
                    text = part
                    break
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end + 1]
        return json.loads(text), None
    except Exception as e:
        return None, str(e)


# ── BÚSQUEDA PRINCIPAL ────────────────────────────────────────────────────────
@csrf_exempt
def ai_search(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        body = json.loads(request.body)
        query = body.get('query', '').strip()
        lang = body.get('lang', 'en')
        if not query:
            return JsonResponse({'found': False, 'message': 'No query provided'})

        SearchHistory.objects.create(query=query, results_count=1)
        wiki = search_wikipedia(query, lang)
        context = wiki['extract'] if wiki else ''

        if lang == 'es':
            prompt = f"""Eres un botánico experto. El usuario busca: "{query}"
Contexto Wikipedia: "{context}"
Si es planta, flor, árbol, hongo o cualquier especie natural → found=true.
Solo found=false si es claramente un objeto (laptop, carro).
Responde SOLO JSON válido sin markdown:
{{"found":true,"common_name":"nombre","scientific_name":"científico","category":"Flores","origin":"país","climate":"Templado","humidity":"Media 40-60%","temperature":"15-25°C","lifespan":"Perenne","description":"2-3 oraciones.","distribution":"Dónde crece.","regions":["Europa"],"unsplash_query":"lily flower","emoji":"🌸"}}"""
        else:
            prompt = f"""You are an expert botanist. User searches: "{query}"
Wikipedia context: "{context}"
If it is a plant, flower, tree, fungus or any natural species → found=true.
Only found=false if clearly NOT a living organism (laptop, car).
Reply ONLY valid JSON, no markdown:
{{"found":true,"common_name":"name","scientific_name":"scientific","category":"Flowers","origin":"country","climate":"Temperate","humidity":"Medium 40-60%","temperature":"15-25°C","lifespan":"Perennial","description":"2-3 sentences.","distribution":"Where it grows.","regions":["Europe"],"unsplash_query":"lily flower","emoji":"🌸"}}"""

        info, err = call_gemini(prompt)
        if err:
            return JsonResponse({'found': False, 'message': err})
        if not info:
            return JsonResponse({'found': False, 'message': f'Could not identify "{query}"'})

        if wiki:
            if wiki.get('image'):
                info['wiki_image'] = wiki['image']
            if wiki.get('url'):
                info['wiki_url'] = wiki['url']

        return JsonResponse(info)
    except Exception as e:
        return JsonResponse({'found': False, 'message': str(e)}, status=500)


def search_species(request):
    return JsonResponse({'results': [], 'query': request.GET.get('q', '')})


def get_search_history(request):
    history = SearchHistory.objects.order_by('-searched_at')[:10]
    return JsonResponse({'history': [
        {'query': h.query, 'searched_at': h.searched_at.strftime('%d/%m %H:%M')}
        for h in history
    ]})


# ── YOLO ──────────────────────────────────────────────────────────────────────
@csrf_exempt
def detect_from_camera(request):
    if request.method == 'POST':
        if not model:
            return JsonResponse({'error': 'YOLO model not loaded'}, status=500)
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cam.release()
        if not ret:
            return JsonResponse({'error': 'No camera access'}, status=400)
        return JsonResponse({'detections': _process_yolo(model(frame), 'camera')})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def detect_from_upload(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_bytes = request.FILES['image'].read()

        # Try Gemini Vision FIRST (mejor para plantas)
        detections = _gemini_vision_identify(image_bytes)

        # Si Gemini falla o no detecta nada, intentar YOLO
        if not detections and model:
            frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            detections = _process_yolo(model(frame), 'upload')

        if detections:
            return JsonResponse({'detections': detections})
        return JsonResponse({'detections': [], 'message': 'No species identified'})
    return JsonResponse({'error': 'No image received'}, status=400)


def _gemini_vision_identify(image_bytes):
    """Use Gemini Vision to identify plant/species from image bytes."""
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY not configured")
        return []
    try:
        import base64
        b64 = base64.b64encode(image_bytes).decode('utf-8')
        prompt = """You are a plant expert. Look at this image and identify any plant, flower, tree, fungus or natural species visible.
Respond ONLY with valid JSON, no markdown:
{"found": true, "species": "Common Name", "scientific": "Scientific name", "confidence": 0.92}
If no plant or natural species is visible, respond: {"found": false}"""

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                ]
            }],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
        }

        print("🔍 Calling Gemini Vision API...")
        r = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"},
                          json=payload, timeout=20)

        if r.status_code != 200:
            print(f"❌ Gemini API error: {r.status_code}")
            return []

        text = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        print(f"📝 Gemini response: {text}")

        # Clean JSON
        if '```' in text:
            for part in text.split('```'):
                part = part.strip().lstrip('json').strip()
                if part.startswith('{'):
                    text = part
                    break

        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(text[start:end + 1])
            if data.get('found') and data.get('species'):
                conf = float(data.get('confidence', 0.88))
                species_name = data['species']
                print(f"✅ Gemini detected: {species_name} ({conf * 100:.1f}%)")

                DetectionResult.objects.create(
                    species_name=species_name, confidence=conf, source='gemini_vision'
                )
                return [{'class': species_name, 'confidence': conf,
                         'confidence_pct': f"{conf * 100:.1f}%",
                         'scientific': data.get('scientific', '')}]
            else:
                print("⚠️ Gemini: No species found in response")
    except Exception as e:
        print(f"❌ Gemini Vision error: {str(e)}")

    return []


def _process_yolo(results, source):
    detections = []
    for r in results:
        for box in r.boxes:
            name = model.names[int(box.cls[0])]
            conf = float(box.conf[0])
            DetectionResult.objects.create(species_name=name, confidence=conf, source=source)
            detections.append({'class': name, 'confidence': conf,
                               'confidence_pct': f"{conf * 100:.1f}%"})
    return sorted(detections, key=lambda x: x['confidence'], reverse=True)


def get_recent_detections(request):
    detections = DetectionResult.objects.order_by('-detected_at')[:10]
    return JsonResponse({'detections': [
        {'species': d.species_name, 'source': d.source,
         'date': d.detected_at.strftime('%d/%m %H:%M')}
        for d in detections
    ]})





