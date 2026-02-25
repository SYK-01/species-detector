
// ==========================================
// OBTENER ELEMENTOS DEL HTML
// Es como hacer variables que "apuntan" a elementos HTML
// Similar a: detector = Detector() en Python
// ==========================================
const cameraMethod = document.getElementById('cameraMethod');
const uploadMethod = document.getElementById('uploadMethod');
const uploadArea = document.getElementById('uploadArea');
const imageInput = document.getElementById('imageInput');
const detectBtn = document.getElementById('detectBtn');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const detectionsList = document.getElementById('detectionsList');

// Variables de estado (como atributos de clase en Python)
let selectedFile = null;
let currentMethod = 'upload';

// ==========================================
// EVENT LISTENERS = "Escuchadores de eventos"
// Es como: if usuario_clickea(boton): hacer_algo()
// ==========================================

// Cuando el usuario clickea "Cámara"
cameraMethod.addEventListener('click', () => {
    cameraMethod.classList.add('active');
    uploadMethod.classList.remove('active');
    uploadArea.classList.remove('active');
    currentMethod = 'camera';
});

// Cuando el usuario clickea "Upload"
uploadMethod.addEventListener('click', () => {
    uploadMethod.classList.add('active');
    cameraMethod.classList.remove('active');
    uploadArea.classList.add('active');
    currentMethod = 'upload';
});

// Cuando clickean el área de upload
uploadArea.addEventListener('click', () => imageInput.click());

// Cuando seleccionan un archivo
imageInput.addEventListener('change', (e) => {
    selectedFile = e.target.files[0];
    if (selectedFile) {
        uploadArea.innerHTML = `
            <div style="font-size: 3em;">✓</div>
            <p style="color: #00f260; font-weight: bold; font-size: 1.2em;">${selectedFile.name}</p>
            <p style="color: rgba(255, 255, 255, 0.5); margin-top: 10px;">Listo para detectar</p>
        `;
    }
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#00f260';
    uploadArea.style.background = 'rgba(0, 242, 96, 0.05)';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'rgba(0, 242, 96, 0.3)';
    uploadArea.style.background = 'rgba(255, 255, 255, 0.02)';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'rgba(0, 242, 96, 0.3)';
    uploadArea.style.background = 'rgba(255, 255, 255, 0.02)';
    selectedFile = e.dataTransfer.files[0];
    if (selectedFile) {
        uploadArea.innerHTML = `
            <div style="font-size: 3em;">✓</div>
            <p style="color: #00f260; font-weight: bold; font-size: 1.2em;">${selectedFile.name}</p>
            <p style="color: rgba(255, 255, 255, 0.5); margin-top: 10px;">Listo para detectar</p>
        `;
    }
});

// ==========================================
// FUNCIÓN PRINCIPAL: DETECTAR
// async/await es como promesas - espera respuesta del servidor
// Similar a hacer una petición HTTP en Python
// ==========================================
detectBtn.addEventListener('click', async () => {
    results.classList.remove('show');
    loading.classList.add('show');
    detectBtn.disabled = true;

    try {
        let response;

        if (currentMethod === 'camera') {
            // Petición a la API de cámara
            response = await fetch('/detect/camera/', {
                method: 'POST'
            });
        } else {
            if (!selectedFile) {
                alert('Por favor selecciona una imagen');
                loading.classList.remove('show');
                detectBtn.disabled = false;
                return;
            }

            // Enviar archivo al servidor
            const formData = new FormData();
            formData.append('image', selectedFile);

            response = await fetch('/detect/upload/', {
                method: 'POST',
                body: formData
            });
        }

        // Convertir respuesta a JSON
        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            displayResults(data.detections);
        }
    } catch (error) {
        alert('Error al detectar: ' + error.message);
    } finally {
        loading.classList.remove('show');
        detectBtn.disabled = false;
    }
});

// ==========================================
// MOSTRAR RESULTADOS
// ==========================================
function displayResults(detections) {
    detectionsList.innerHTML = '';

    if (detections.length === 0) {
        detectionsList.innerHTML = '<p style="text-align: center; color: #8b9dc3;">No se detectaron especies</p>';
    } else {
        detections.forEach(det => {
            const item = document.createElement('div');
            item.className = 'detection-item';
            item.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; color: #fff; font-size: 1.1em;">${det.class}</span>
                    <span style="color: #00f260;">Confianza: ${(det.confidence * 100).toFixed(1)}%</span>
                </div>
            `;
            detectionsList.appendChild(item);
        });
    }

    results.classList.add('show');
}

























