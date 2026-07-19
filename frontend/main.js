document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Metadata for dropdowns
    let hierarchy = {};
    try {
        const metaResp = await fetch('/api/metadata');
        if (metaResp.ok) {
            const data = await metaResp.json();
            hierarchy = data.hierarchy;
            
            // Populate Make
            const makeSelect = document.getElementById('make');
            makeSelect.innerHTML = '<option disabled selected value="">Select Brand</option>';
            Object.keys(hierarchy).sort().forEach(make => {
                const opt = document.createElement('option');
                opt.value = make;
                opt.textContent = make;
                makeSelect.appendChild(opt);
            });
            
            // Handle Make change
            makeSelect.addEventListener('change', (e) => {
                const selectedMake = e.target.value;
                const models = hierarchy[selectedMake];
                const variantSelect = document.getElementById('model_variant');
                
                variantSelect.innerHTML = '<option disabled selected value="">Select Model & Variant</option>';
                variantSelect.disabled = false;
                
                Object.keys(models).sort().forEach(model => {
                    const group = document.createElement('optgroup');
                    group.label = model;
                    
                    models[model].forEach(variant => {
                        const opt = document.createElement('option');
                        opt.value = `${model}|${variant}`;
                        opt.textContent = `${model} ${variant}`;
                        group.appendChild(opt);
                    });
                    
                    variantSelect.appendChild(group);
                });
            });
            
            // Populate City
            const citySelect = document.getElementById('city');
            citySelect.innerHTML = '<option disabled selected value="">Select City</option>';
            data.cities.forEach(city => {
                const opt = document.createElement('option');
                opt.value = city;
                opt.textContent = city;
                citySelect.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Failed to fetch metadata:", e);
    }

    // ---- Frame Animation Logic ----
    const canvas = document.getElementById('video-canvas');
    const context = canvas.getContext('2d');
    const frameCount = 201;
    
    // Preload images
    const frames = [];
    let loadedFrames = 0;
    let initialized = false;

    for (let i = 1; i <= frameCount; i++) {
        const img = new Image();
        // Pad with zeros: 001 to 201
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
        
        // Map the scrollY across the ENTIRE scrollable height of the page
        const maxScroll = Math.max(document.body.scrollHeight - window.innerHeight, 1);
        let progress = Math.min(Math.max(scrollY / maxScroll, 0), 1);
        
        // Fade out hero text quickly in the first 20% of the scroll
        const heroText = document.getElementById('hero-text');
        if (heroText) {
            heroText.style.opacity = Math.max(1 - (progress * 5), 0);
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

    // Make sliders interactive by filling the track
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        const updateSlider = (el) => {
            const val = el.value;
            const percentage = (val / 10) * 100;
            // Apple style blue track fill
            el.style.background = `linear-gradient(to right, #0A84FF 0%, #0A84FF ${percentage}%, rgba(255, 255, 255, 0.1) ${percentage}%, rgba(255, 255, 255, 0.1) 100%)`;
            
            // Update textual label
            let labelText = "Average";
            if (val >= 9) labelText = "Like New";
            else if (val >= 7) labelText = "Good";
            else if (val >= 4) labelText = "Average";
            else labelText = "Needs Repair";
            
            const textElement = el.parentElement.querySelector('.condition-text');
            if (textElement) textElement.innerText = labelText;
        };
        
        // Initial call
        updateSlider(slider);
        
        slider.addEventListener('input', (e) => {
            updateSlider(e.target);
            const valDisplay = document.getElementById(`val-${e.target.name}`);
            if (valDisplay) valDisplay.innerText = e.target.value;
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Loading state with Apple-like spinner
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="flex items-center justify-center gap-2"><span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span> Processing...</span>';
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.8';
        
        const formData = new FormData(form);
        
        const modelVariantRaw = formData.get('model_variant');
        const [modelStr, variantStr] = modelVariantRaw ? modelVariantRaw.split('|') : ["Unknown", "Standard"];

        const features = {
            make: formData.get('make'),
            model: modelStr, 
            variant: variantStr,
            city: formData.get('city'),
            year: parseInt(formData.get('year')),
            mileage: parseInt(formData.get('mileage')),
            fuel_type: formData.get('fuel_type'),
            transmission: "Manual",
            body_type: "Hatchback",
            no_of_owners: parseInt(formData.get('no_of_owners')),
            engine_transmission_chassis: parseFloat(formData.get('engine')),
            fuel_ignition_other: parseFloat(formData.get('fuel')),
            interiors_ac: parseFloat(formData.get('interiors')),
            exteriors_lights: parseFloat(formData.get('exteriors')),
            tyres_clutch_brakes: parseFloat(formData.get('tyres')),
            meter_not_tampered: formData.get('meter_not_tampered') ? 1 : 0,
            non_flooded: formData.get('non_flooded') ? 1 : 0,
            core_structure_intact: formData.get('core_structure_intact') ? 1 : 0
        };

        try {
            const response = await fetch('/api/predict', {
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
                featuresHTML += '<div class="font-medium mb-3 text-white/60 text-xs uppercase tracking-wider">Factors considered in this estimate</div>';
                featuresHTML += '<div class="flex flex-col gap-3">';
                for (const [feat, val] of topFeatures) {
                    const percentage = (val * 100).toFixed(1);
                    const cleanFeat = feat.replace('num__', '').replace('cat__', '').replace('remainder__', '').replace(/_/g, ' ');
                    featuresHTML += `
                        <div class="flex flex-col gap-1">
                            <div class="flex justify-between capitalize text-white/90 text-xs">
                                <span>${cleanFeat}</span>
                                <span class="text-[#0A84FF] font-medium">${percentage}% impact</span>
                            </div>
                            <div class="w-full bg-white/10 rounded-full h-1.5">
                                <div class="bg-[#0A84FF] h-1.5 rounded-full" style="width: ${percentage}%"></div>
                            </div>
                        </div>
                    `;
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
                        Estimated Market Range: ${formatCI(data.confidence_interval[0])} - ${formatCI(data.confidence_interval[1])}
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
