document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('video-canvas');
    if (!canvas) return;
    
    const context = canvas.getContext('2d');
    const frameCount = 201;
    const frames = [];
    let currentFrame = 0;
    
    const resizeCanvas = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    const drawFrame = (img) => {
        if (!img || !img.complete || img.naturalHeight === 0) return;
        const w = canvas.width;
        const h = canvas.height;
        const imgRatio = img.width / img.height;
        const canvasRatio = w / h;
        
        let drawW, drawH, drawX, drawY;
        
        if (canvasRatio > imgRatio) {
            drawW = w;
            drawH = (w / imgRatio);
        } else {
            drawW = (h * imgRatio);
            drawH = h;
        }
        drawX = (w - drawW) / 2;
        drawY = (h - drawH) / 2;
        
        context.clearRect(0, 0, w, h);
        context.drawImage(img, drawX, drawY, drawW, drawH);
    };
    
    let playing = false;
    
    const loop = () => {
        // Find nearest loaded frame if current isn't loaded yet
        let imgToDraw = frames[currentFrame];
        if (!imgToDraw || !imgToDraw.complete) {
            for(let i = currentFrame; i >= 0; i--) {
                if (frames[i] && frames[i].complete) {
                    imgToDraw = frames[i];
                    break;
                }
            }
        }
        
        if (imgToDraw) {
            drawFrame(imgToDraw);
        }
        
        currentFrame = (currentFrame + 1) % frameCount;
        setTimeout(() => requestAnimationFrame(loop), 33); // ~30 fps
    };
    
    // Stagger loading to prevent blocking
    const loadFrames = () => {
        let i = 1;
        const loadNext = () => {
            if (i > frameCount) return;
            const img = new Image();
            const frameNum = i.toString().padStart(3, '0');
            img.src = `/frames/ezgif-frame-${frameNum}.png`;
            
            img.onload = () => {
                frames[i-1] = img;
                if (i === 5 && !playing) {
                    playing = true;
                    canvas.style.opacity = '1';
                    loop();
                }
                i++;
                loadNext(); // Load next sequentially
            };
            img.onerror = () => {
                i++;
                loadNext();
            };
        };
        loadNext();
    };
    
    loadFrames();
});
