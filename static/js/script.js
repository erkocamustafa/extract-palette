const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const uploadState = document.getElementById('uploadState');
const previewState = document.getElementById('previewState');
const sourceImage = document.getElementById('sourceImage');
const colorGrid = document.getElementById('colorGrid');
const popover = document.getElementById('colorPopover');

let currentColors = [];
let currentPercentages = [];
let currentFormat = 'css'; 

// DRAG & DROP
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.background = '#eef2ff'; });
dropZone.addEventListener('dragleave', () => { dropZone.style.background = '#f1f5f9'; });
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.background = '#f1f5f9';
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
uploadState.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => { if (fileInput.files.length) handleFile(fileInput.files[0]); });

function handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        sourceImage.src = e.target.result;
        uploadState.classList.add('hidden');
        previewState.classList.remove('hidden');
        sourceImage.onload = () => {
            document.getElementById('imgWidth').innerText = sourceImage.naturalWidth;
            document.getElementById('imgHeight').innerText = sourceImage.naturalHeight;
        }
    };
    reader.readAsDataURL(file);
    uploadImageToBackend(file);
}

function uploadImageToBackend(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    // Skeleton loading states
    colorGrid.innerHTML = Array(5).fill('<div class="color-box skeleton"></div>').join('');
    document.getElementById('codeOutput').innerText = 'Generating palette...';
    
    fetch('/analyze', { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
        if (data.success) updateUI(data.data);
    })
    .catch(err => console.error(err));
}

function updateUI(data) {
    currentColors = data.colors;
    currentPercentages = data.percentages || []; // Hata önlemek için boş dizi kontrolü
    colorGrid.innerHTML = '';
    
    // PALETTE
    data.colors.forEach((color, index) => {
        const box = document.createElement('div');
        box.className = 'color-box';
        box.style.backgroundColor = color;
        
        // --- DEĞİŞEN KISIM BURASI ---
        // CSS Tooltip için veriyi 'data-percent' içine yazıyoruz
        if (currentPercentages.length > index) {
            box.setAttribute('data-percent', `%${currentPercentages[index]}`);
        } else {
            box.setAttribute('data-percent', '');
        }
        // -----------------------------
        
        box.onclick = (e) => { openPopover(e.target, color); e.stopPropagation(); };
        colorGrid.appendChild(box);
    });

    // AVG TINT
    const avgBox = document.getElementById('avgColorBox');
    const avgWrapper = document.getElementById('avgWrapper');
    avgBox.style.backgroundColor = data.average;
    avgBox.classList.remove('skeleton');
    document.getElementById('avgHex').innerText = data.average;
    avgWrapper.onclick = (e) => { openPopover(avgWrapper, data.average); e.stopPropagation(); }
    
    // INFO
    document.getElementById('usageText').innerText = data.usage;
    document.getElementById('usageText').classList.remove('text-blur');
    document.getElementById('contrastText').innerText = data.contrast;
    document.getElementById('contrastText').classList.remove('text-blur');

    // GRADIENT
    const c1 = data.colors[0];
    const c2 = data.colors[1];
    const gradCSS = `linear-gradient(135deg, ${c1}, ${c2})`;
    document.getElementById('gradientPreview').style.background = gradCSS;
    document.getElementById('gradientCode').innerText = `background: ${gradCSS};`;
    window.currentGradient = `background: ${gradCSS};`;

    generateCode();
}

// --- YENİ: Palette İndirme ---
window.downloadPaletteImage = function() {
    if (currentColors.length === 0) {
        showToast("No palette generated yet!");
        return;
    }

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const width = 1000;
    const height = 300;
    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);

    const boxWidth = width / currentColors.length;
    
    currentColors.forEach((color, i) => {
        ctx.fillStyle = color;
        ctx.fillRect(i * boxWidth, 0, boxWidth, height - 50);
        
        ctx.fillStyle = "#0f172a";
        ctx.font = "bold 16px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(color, (i * boxWidth) + (boxWidth / 2), height - 30);
        
        if (currentPercentages.length > i) {
            ctx.font = "12px Inter, sans-serif";
            ctx.fillStyle = "#64748b";
            ctx.fillText(`${currentPercentages[i]}%`, (i * boxWidth) + (boxWidth / 2), height - 12);
        }
    });

    const link = document.createElement('a');
    link.download = 'my-palette.png';
    link.href = canvas.toDataURL();
    link.click();
    
    showToast("Palette Image Downloaded! 🖼️");
}

// POPOVER & MODAL
function openPopover(target, hex) {
    document.getElementById('popHex').innerText = hex;
    document.getElementById('popRgb').innerText = hexToRgb(hex);
    document.getElementById('popColorPreview').style.backgroundColor = hex;
    const rect = target.getBoundingClientRect();
    let top = rect.bottom + 10;
    let left = rect.left + (rect.width / 2) - 110;
    popover.style.top = top + 'px';
    popover.style.left = left + 'px';
    popover.classList.add('active');
}
function closePopover() { popover.classList.remove('active'); }

document.addEventListener('click', (e) => {
    if (!popover.contains(e.target) && !e.target.closest('#avgWrapper') && !e.target.closest('.color-box')) closePopover();
    if (e.target.classList.contains('modal-overlay')) closeModal('howItWorksModal');
});

window.openModal = function(id) { document.getElementById(id).classList.add('active'); }
window.closeModal = function(id) { document.getElementById(id).classList.remove('active'); }

// HELPERS
function hexToRgb(hex) {
    let r = 0, g = 0, b = 0;
    if (hex.length == 4) { r = "0x"+hex[1]+hex[1]; g = "0x"+hex[2]+hex[2]; b = "0x"+hex[3]+hex[3]; } 
    else if (hex.length == 7) { r = "0x"+hex[1]+hex[2]; g = "0x"+hex[3]+hex[4]; b = "0x"+hex[5]+hex[6]; }
    return +r + ", " + +g + ", " + +b;
}

window.copyFromPop = function(type) {
    let text = type === 'hex' ? document.getElementById('popHex').innerText : document.getElementById('popRgb').innerText;
    navigator.clipboard.writeText(text);
    showToast(`${text} copied!`);
    closePopover();
}
window.copyGradient = function() {
    if(window.currentGradient) { navigator.clipboard.writeText(window.currentGradient); showToast('Gradient Copied!'); }
}
function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

// CODE GEN
function generateCode() {
    const output = document.getElementById('codeOutput');
    let code = '';
    if (currentFormat === 'css') {
        code = `:root {\n`;
        currentColors.forEach((c, i) => code += `  --color-${i+1}: ${c};\n`);
        code += `}`;
    } else if (currentFormat === 'tailwind') {
        code = `colors: {\n`;
        currentColors.forEach((c, i) => code += `  'brand-${i+1}': '${c}',\n`);
        code += `}`;
    } else { code = JSON.stringify(currentColors, null, 2); }
    output.innerText = code;
}
window.switchTab = function(format, element) {
    currentFormat = format;
    document.querySelectorAll('.m-tab').forEach(btn => btn.classList.remove('active'));
    if(element) element.classList.add('active');
    if(currentColors.length) generateCode();
}
window.copyCodeBlock = function() {
    navigator.clipboard.writeText(document.getElementById('codeOutput').innerText);
    showToast('Code block copied!');
}

document.getElementById('resetBtn').addEventListener('click', () => {
    uploadState.classList.remove('hidden');
    previewState.classList.add('hidden');
    fileInput.value = '';
    currentColors = [];
    document.getElementById('codeOutput').innerText = 'Upload an image...';
    closePopover();
});