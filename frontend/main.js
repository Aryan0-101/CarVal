document.addEventListener('DOMContentLoaded', () => {
    // ---- Frame Animation Logic ----
    const canvas = document.getElementById('video-canvas');
    const context = canvas.getContext('2d');
    const frameCount = 130;
    
    // Preload images
    const frames = [];
    let loadedFrames = 0;
    let initialized = false;

    for (let i = 1; i <= frameCount; i++) {
        const img = new Image();
        // Pad with zeros: 001 to 130
        const frameNum = i.toString().padStart(3, '0');
        img.src = `/frames/ezgif-frame-${frameNum}.png`;
        img.onload = () => {
            loadedFrames++;
            if (loadedFrames === 1 && !initialized) {
                // Initialize canvas on first frame load
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
                updateImage(0);
                initialized = true;
            }
        };
        frames.push(img);
    }

    window.addEventListener('resize', () => {
        if (!initialized) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        updateImage(window.scrollY);
    });

    const updateImage = (scrollY) => {
        if (!initialized || frames.length === 0) return;
        
        // The scroll container is 300vh, content starts at 100vh.
        // We'll map the scrollY from 0 to 100vh to frames 0 to 129.
        const maxScroll = window.innerHeight;
        let progress = Math.min(Math.max(scrollY / maxScroll, 0), 1);
        
        // Fade out hero text
        const heroText = document.getElementById('hero-text');
        if (heroText) {
            heroText.style.opacity = 1 - (progress * 2);
        }

        const frameIndex = Math.min(
            frameCount - 1,
            Math.floor(progress * frameCount)
        );
        
        const img = frames[frameIndex];
        // If this specific frame hasn't loaded yet, try to find the nearest loaded one (fallback)
        if (!img || !img.complete || img.naturalHeight === 0) {
            // Find closest
            let fallback = frames[0];
            for (let i = frameIndex; i >= 0; i--) {
                if (frames[i] && frames[i].complete && frames[i].naturalHeight !== 0) {
                    fallback = frames[i];
                    break;
                }
            }
            if (!fallback || !fallback.complete || fallback.naturalHeight === 0) return; // give up
            drawFrame(fallback, progress);
        } else {
            drawFrame(img, progress);
        }
    };

    const drawFrame = (img, progress) => {
        const w = canvas.width;
        const h = canvas.height;
        const imgRatio = img.width / img.height;
        const canvasRatio = w / h;
        
        // Slight scale effect as it scrolls (Apple style subtle zoom)
        const scale = 1 + (progress * 0.1); 
        
        let drawW, drawH, drawX, drawY;
        
        if (canvasRatio > imgRatio) {
            drawW = w * scale;
            drawH = (w / imgRatio) * scale;
        } else {
            drawW = (h * imgRatio) * scale;
            drawH = h * scale;
        }
        
        drawX = (w - drawW) / 2;
        drawY = (h - drawH) / 2;
        
        context.clearRect(0, 0, w, h);
        context.drawImage(img, drawX, drawY, drawW, drawH);
        
        // Darken as we scroll down so the form remains legible
        if (progress > 0) {
            // max opacity 0.8
            context.fillStyle = `rgba(0, 0, 0, ${progress * 0.8})`;
            context.fillRect(0, 0, w, h);
        }
    };

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


    // ---- Form Submission Logic ----
    const form = document.getElementById('predict-form');
    const resultDisplayContainer = document.getElementById('result-display-container');
    const resultDisplay = document.getElementById('result-display');
    const submitBtn = form.querySelector('.submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Loading state with Apple-like spinner
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="flex items-center justify-center gap-2"><span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span> Processing...</span>';
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.8';
        
        const formData = new FormData(form);
        const avgScore = parseFloat(formData.get('avg_inspection_score'));
        
        const features = {
            make: formData.get('make'),
            model: "Unknown", 
            year: parseInt(formData.get('year')),
            mileage: parseInt(formData.get('mileage')),
            fuel_type: formData.get('fuel_type'),
            transmission: "Manual",
            body_type: "Hatchback",
            no_of_owners: parseInt(formData.get('no_of_owners')),
            engine_transmission_chassis: avgScore,
            fuel_ignition_other: avgScore,
            interiors_ac: avgScore,
            exteriors_lights: avgScore,
            tyres_clutch_brakes: avgScore
        };

        try {
            const response = await fetch('http://localhost:8000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(features)
            });

            if (!response.ok) throw new Error('API Error');
            
            const data = await response.json();
            
            const formatCI = val => new Intl.NumberFormat('en-IN', {
                style: 'currency', currency: 'INR', maximumFractionDigits: 0
            }).format(val);

            const formattedPrice = formatCI(data.predicted_price);

            // Sort feature importance
            const topFeatures = Object.entries(data.feature_importance || {})
                .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                .slice(0, 3);

            let featuresHTML = '';
            if (topFeatures.length > 0) {
                featuresHTML = '<div class="mt-4 text-sm text-left bg-white/5 p-4 rounded-xl border border-white/10">';
                featuresHTML += '<div class="font-medium mb-3 text-white/60 text-xs uppercase tracking-wider">Top Pricing Factors</div>';
                featuresHTML += '<div class="flex flex-col gap-2">';
                for (const [feat, val] of topFeatures) {
                    const impact = val > 0 ? `<span class="text-[#32d74b] font-medium">+${formatCI(val)}</span>` : `<span class="text-[#ff453a] font-medium">${formatCI(val)}</span>`;
                    const cleanFeat = feat.replace('num__', '').replace('cat__', '').replace('remainder__', '').replace(/_/g, ' ');
                    featuresHTML += `<div class="flex justify-between capitalize text-white/90"><span>${cleanFeat}</span> ${impact}</div>`;
                }
                featuresHTML += '</div></div>';
            }

            // Render Result
            resultDisplayContainer.classList.remove('hidden');
            resultDisplayContainer.classList.add('enter-stage');
            
            resultDisplay.innerHTML = `
                <div class="text-center">
                    <div class="text-white/60 uppercase tracking-wider text-xs font-semibold mb-2">Estimated Market Value</div>
                    <div class="text-5xl font-bold text-white tracking-tight mb-2">${formattedPrice}</div>
                    <p class="text-white/50 text-sm">
                        90% Confidence Interval: ${formatCI(data.confidence_interval[0])} - ${formatCI(data.confidence_interval[1])}
                    </p>
                    ${featuresHTML}
                </div>
            `;

            // Smooth scroll to results
            resultDisplayContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        } catch (err) {
            resultDisplayContainer.classList.remove('hidden');
            resultDisplayContainer.classList.add('enter-stage');
            resultDisplay.innerHTML = `
                <div class="text-center text-[#ff453a] p-4 bg-[#ff453a]/10 rounded-xl border border-[#ff453a]/20">
                    <p class="font-medium">Failed to connect to valuation engine.</p>
                    <small class="opacity-80">Make sure the backend is running on port 8000.</small>
                </div>
            `;
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
        }
    });
});
