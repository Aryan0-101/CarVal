document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('video-canvas');
    if (!canvas) return;
    
    const context = canvas.getContext('2d');
    const frameCount = 201;
    const frames = [];
    let maxScroll = 1;
    let initialized = false;

    const updateMaxScroll = () => {
        // The total scrollable distance
        maxScroll = Math.max(document.body.scrollHeight - window.innerHeight, 1);
    };

    const drawFrame = (img, progress) => {
        if (!img || !img.complete || img.naturalHeight === 0) return;
        const w = canvas.width;
        const h = canvas.height;
        const imgRatio = img.width / img.height;
        const canvasRatio = w / h;
        
        // Slight zoom based on scroll progress to add dynamic feel
        const scale = 1 + (progress * 0.1); 
        let drawW, drawH, drawX, drawY;
        
        // Use 'contain' style scaling so the car isn't cropped out on mobile screens
        const baseScale = Math.min(w / img.width, h / img.height);
        
        // Slightly enlarge it so it feels immersive. On mobile (portrait), enlarge a bit more so it fills the width nicely.
        const mobileMultiplier = (h > w) ? 1.8 : 1.2;
        const finalScale = baseScale * mobileMultiplier * scale;
        
        drawW = img.width * finalScale;
        drawH = img.height * finalScale;
        drawX = (w - drawW) / 2;
        drawY = (h - drawH) / 2;
        
        context.clearRect(0, 0, w, h);
        context.drawImage(img, drawX, drawY, drawW, drawH);
    };

    const updateImage = (scrollY) => {
        if (!initialized || frames.length === 0) return;
        let progress = Math.min(Math.max(scrollY / maxScroll, 0), 1);
        
        // Map progress to frame index
        const frameIndex = Math.min(frameCount - 1, Math.floor(progress * frameCount));
        
        let img = frames[frameIndex];
        // If exact frame isn't loaded, fallback to nearest loaded previous frame
        if (!img || !img.complete || img.naturalHeight === 0) {
            for (let i = frameIndex; i >= 0; i--) {
                if (frames[i] && frames[i].complete && frames[i].naturalHeight !== 0) {
                    img = frames[i];
                    break;
                }
            }
        }
        if (img) drawFrame(img, progress);
    };

    const resizeCanvas = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        updateMaxScroll();
        if (initialized) updateImage(window.scrollY);
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initial frame load
    const firstImg = new Image();
    firstImg.src = `/frames/ezgif-frame-001.png`;
    firstImg.onload = () => {
        frames[0] = firstImg;
        initialized = true;
        updateImage(window.scrollY);
        canvas.style.opacity = '1';
    };

    // Lazy load remaining frames
    window.addEventListener('load', () => {
        let currentFrame = 2;
        const loadNext = () => {
            if (currentFrame > frameCount) return;
            const img = new Image();
            const frameNum = currentFrame.toString().padStart(3, '0');
            img.src = `/frames/ezgif-frame-${frameNum}.png`;
            
            img.onload = () => {
                frames[currentFrame - 1] = img;
                currentFrame++;
                setTimeout(loadNext, 10);
            };
            img.onerror = () => {
                currentFrame++;
                setTimeout(loadNext, 10);
            }
        };
        
        if ('requestIdleCallback' in window) {
            requestIdleCallback(loadNext);
        } else {
            setTimeout(loadNext, 500);
        }
    });

    // Scroll event with requestAnimationFrame for performance
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateImage(window.scrollY);
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
});
