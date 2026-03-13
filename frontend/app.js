/**
 * CV NEXUS - Frontend Application
 * Protocolos de Seguridad y Gestión de CVs
 */

// Estado de la aplicación
const state = {
    token: localStorage.getItem('token'),
    userEmail: localStorage.getItem('userEmail')
};

// Mapeo de errores amigables
const ERROR_MAP = {
    'Invalid credentials': 'Las credenciales no son válidas. Verifique su correo y contraseña.',
    'User already exists': 'Este correo ya está registrado en el sistema.',
    'No tiene ningún CV subido': 'No se encontró ningún documento vinculado a su perfil.',
    'Invalid token': 'Su sesión ha expirado. Por favor, ingrese de nuevo.',
    'Could not validate credentials': 'Error de autenticación. Inicie sesión de nuevo.',
    'Only PDF files are allowed': 'Formato no soportado. Por favor, suba un archivo PDF.',
    'File too large': 'El archivo excede el límite de 5.0 MB permitido.',
    'Rate limit exceeded': 'Demasiadas solicitudes. Por favor, espere un momento.',
    'Access denied': 'Acceso denegado por protocolos de seguridad.',
    'Ha ocurrido un error interno': 'Error en el nexo central. Inténtelo más tarde.'
};

function getFriendlyError(message) {
    return ERROR_MAP[message] || message || 'Error desconocido en el sistema.';
}

// Elementos del DOM
const elements = {
    // Auth
    authSection: document.getElementById('auth-section'),
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    loginError: document.getElementById('login-error'),
    registerError: document.getElementById('register-error'),
    registerSuccess: document.getElementById('register-success'),
    tabs: document.querySelectorAll('.tab'),

    // Dashboard
    dashboardSection: document.getElementById('dashboard-section'),
    navMenu: document.getElementById('nav-menu'),
    userEmailSpan: document.getElementById('user-email'),
    logoutBtn: document.getElementById('logout-btn'),

    // CV
    cvInfo: document.getElementById('cv-info'),
    noCv: document.getElementById('no-cv'),
    cvFilename: document.getElementById('cv-filename'),
    cvDate: document.getElementById('cv-date'),
    uploadForm: document.getElementById('upload-form'),
    uploadError: document.getElementById('upload-error'),
    uploadSuccess: document.getElementById('upload-success'),
    downloadCvBtn: document.getElementById('download-cv-btn'),
    deleteCvBtn: document.getElementById('delete-cv-btn'),
    // Preview Elements
    dropZone: document.getElementById('drop-zone'),
    dropContent: document.getElementById('drop-content'),
    filePreview: document.getElementById('file-preview'),
    previewFilename: document.getElementById('preview-filename'),
    pdfViewer: document.getElementById('pdf-preview-viewer'),
    removeFileBtn: document.getElementById('remove-file-btn')
};

// API Base URL
const API_BASE = '/api';

// Utilidades UI
function showError(element, message) {
    element.textContent = getFriendlyError(message);
    element.classList.remove('hidden');
    // Scroll suave al error
    element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError(element) {
    element.classList.add('hidden');
}

function showSuccess(element, message) {
    element.textContent = message;
    element.classList.remove('hidden');
}

function hideSuccess(element) {
    element.classList.add('hidden');
}

function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

// API Functions
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        ...options.headers
    };

    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }

    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Manejar errores de sesión expirada
        if (response.status === 401 && state.token) {
            logout();
            throw new Error('Su sesión ha expirado');
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.detail || 'Error en la solicitud');
        }

        return data;
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// Auth Functions
async function login(email, password) {
    const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });

    state.token = data.access_token;
    state.userEmail = email;
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('userEmail', email);

    showDashboard();
}

async function register(email, password) {
    await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
}

function logout() {
    state.token = null;
    state.userEmail = null;
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');

    clearAllForms();
    showAuth();
}

// CV Functions
async function loadCVInfo() {
    try {
        const data = await apiRequest('/cv/info');
        elements.cvFilename.textContent = sanitizeHTML(data.original_filename);
        elements.cvDate.textContent = new Date(data.uploaded_at).toLocaleString('es-ES', {
            year: 'numeric', month: 'long', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
        elements.cvInfo.classList.remove('hidden');
        elements.noCv.classList.add('hidden');
    } catch (error) {
        elements.cvInfo.classList.add('hidden');
        elements.noCv.classList.remove('hidden');
    }
}

async function uploadCV(file) {
    const formData = new FormData();
    formData.append('file', file);

    await apiRequest('/cv/upload', {
        method: 'POST',
        body: formData
    });

    await loadCVInfo();
}

async function downloadCV() {
    try {
        const response = await fetch(`${API_BASE}/cv/download`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Error al descargar');
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'documento_cv.pdf';

        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);
            if (match) {
                filename = decodeURIComponent(match[1]);
            }
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        showError(elements.uploadError, error.message);
    }
}

async function deleteCV() {
    if (!confirm('¿Confirma la eliminación permanente de este documento?')) {
        return;
    }

    try {
        await apiRequest('/cv/delete', {
            method: 'DELETE'
        });
        await loadCVInfo();
        showSuccess(elements.uploadSuccess, 'Documento eliminado correctamente.');
        setTimeout(() => hideSuccess(elements.uploadSuccess), 3000);
    } catch (error) {
        showError(elements.uploadError, 'Error al procesar la eliminación.');
    }
}

// UI Helper Functions
function resetUploadUI() {
    if (elements.filePreview) {
        elements.filePreview.classList.add('hidden');
        elements.dropContent.classList.remove('hidden');
        if (elements.pdfViewer) elements.pdfViewer.src = '';
        const fileInput = document.getElementById('cv-file');
        if (fileInput) fileInput.value = '';
    }
}

function clearCVDisplay() {
    elements.cvFilename.textContent = '';
    elements.cvDate.textContent = '';
    elements.cvInfo.classList.add('hidden');
    elements.noCv.classList.add('hidden');
}

function clearAllForms() {
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => input.value = '');
    
    // Resetear botones de envío a su estado original
    const loginBtn = elements.loginForm.querySelector('button[type="submit"]');
    if (loginBtn) {
        loginBtn.textContent = 'Ingresar al Sistema';
        loginBtn.disabled = false;
    }
    
    const registerBtn = elements.registerForm.querySelector('button[type="submit"]');
    if (registerBtn) {
        registerBtn.textContent = 'Crear Cuenta';
        registerBtn.disabled = false;
    }
}

function clearAllMessages() {
    hideError(elements.loginError);
    hideError(elements.registerError);
    hideError(elements.uploadError);
    hideSuccess(elements.registerSuccess);
    hideSuccess(elements.uploadSuccess);
    
    // Reset preview
    resetUploadUI();
}

// UI Functions
function showAuth() {
    clearCVDisplay();
    clearAllMessages();

    elements.authSection.classList.remove('hidden');
    elements.dashboardSection.classList.add('hidden');
    elements.navMenu.classList.add('hidden');
}

function showDashboard() {
    clearCVDisplay();
    clearAllMessages();

    elements.authSection.classList.add('hidden');
    elements.dashboardSection.classList.remove('hidden');
    elements.navMenu.classList.remove('hidden');
    elements.userEmailSpan.textContent = sanitizeHTML(state.userEmail);

    loadCVInfo();
}

function switchTab(tabName) {
    elements.tabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    if (tabName === 'login') {
        elements.loginForm.classList.remove('hidden');
        elements.registerForm.classList.add('hidden');
    } else {
        elements.loginForm.classList.add('hidden');
        elements.registerForm.classList.remove('hidden');
    }

    clearAllMessages();
}

// Event Listeners
elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

// Drag and Drop & Preview Logic
const cvFileInput = document.getElementById('cv-file');

function handleFileSelect(file) {
    if (file && file.type === 'application/pdf') {
        elements.previewFilename.textContent = sanitizeHTML(file.name);
        
        // Crear URL para el visor
        const fileURL = URL.createObjectURL(file);
        elements.pdfViewer.src = fileURL;
        
        elements.dropContent.classList.add('hidden');
        elements.filePreview.classList.remove('hidden');
        hideError(elements.uploadError);
    } else if (file) {
        showError(elements.uploadError, 'Por favor, selecciona un archivo PDF válido.');
        resetUploadUI();
    }
}

if (cvFileInput) {
    cvFileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });
}

if (elements.dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        elements.dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        elements.dropZone.addEventListener(eventName, () => {
            elements.dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        elements.dropZone.addEventListener(eventName, () => {
            elements.dropZone.classList.remove('dragover');
        }, false);
    });

    elements.dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        if (file) {
            cvFileInput.files = dt.files; // Sincronizar con el input
            handleFileSelect(file);
        }
    });
}

if (elements.removeFileBtn) {
    elements.removeFileBtn.addEventListener('click', (e) => {
        e.preventDefault();
        resetUploadUI();
    });
}

elements.loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError(elements.loginError);

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    const btn = elements.loginForm.querySelector('button');
    const originalText = btn.textContent;
    btn.textContent = 'Autenticando...';
    btn.disabled = true;

    try {
        await login(email, password);
    } catch (error) {
        showError(elements.loginError, error.message);
        btn.textContent = originalText;
        btn.disabled = false;
    }
});

elements.registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError(elements.registerError);
    hideSuccess(elements.registerSuccess);

    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const passwordConfirm = document.getElementById('register-password-confirm').value;

    if (password !== passwordConfirm) {
        showError(elements.registerError, 'Las contraseñas no coinciden.');
        return;
    }

    const btn = elements.registerForm.querySelector('button');
    btn.disabled = true;

    try {
        await register(email, password);
        showSuccess(elements.registerSuccess, 'Registro exitoso. Proceda a iniciar sesión.');
        setTimeout(() => switchTab('login'), 2000);
    } catch (error) {
        showError(elements.registerError, error.message);
        btn.disabled = false;
    }
});

elements.logoutBtn.addEventListener('click', logout);

elements.uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError(elements.uploadError);
    hideSuccess(elements.uploadSuccess);

    const file = cvFileInput.files[0];

    if (!file) {
        showError(elements.uploadError, 'Seleccione un archivo válido.');
        return;
    }

    const btn = elements.uploadForm.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'Encriptando y Subiendo...';
    btn.disabled = true;

    try {
        await uploadCV(file);
        showSuccess(elements.uploadSuccess, 'Sincronización de CV completada con éxito.');
        resetUploadUI();
    } catch (error) {
        showError(elements.uploadError, error.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
});

elements.downloadCvBtn.addEventListener('click', downloadCV);
elements.deleteCvBtn.addEventListener('click', deleteCV);

// Inicialización
if (state.token) {
    apiRequest('/auth/me')
        .then(() => showDashboard())
        .catch(() => logout());
} else {
    showAuth();
}
