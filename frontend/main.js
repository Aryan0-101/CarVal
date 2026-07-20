document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Metadata for dropdowns
    let hierarchy = {};
    const API_BASE = import.meta.env.VITE_API_URL || 'https://museum-chronicles-folder-painted.trycloudflare.com';
    
    try {
        const metaResp = await fetch(`${API_BASE}/api/metadata`);
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

    // ---- Optimized Frame Animation Logic ----
    const canvas = document.getElementById('video-canvas');
    let updateMaxScroll = () => {};
    
    if (canvas) {
        const context = canvas.getContext('2d');
        const frameCount = 201;
        const frames = [];
        let maxScroll = 1;
        let initialized = false;

        updateMaxScroll = () => {
            maxScroll = Math.max(document.body.scrollHeight - window.innerHeight, 1);
        };

        const drawFrame = (img, progress) => {
            if (!img || !img.complete || img.naturalHeight === 0) return;
            const w = canvas.width;
            const h = canvas.height;
            const imgRatio = img.width / img.height;
            const canvasRatio = w / h;
            
            const scale = 1 + (progress * 0.05); 
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
        };

        const updateImage = (scrollY) => {
            if (!initialized || frames.length === 0) return;
            let progress = Math.min(Math.max(scrollY / maxScroll, 0), 1);
            const frameIndex = Math.min(frameCount - 1, Math.floor(progress * frameCount));
            
            let img = frames[frameIndex];
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

        // Initialize immediately with just the first frame
        const firstImg = new Image();
        firstImg.src = `/frames/ezgif-frame-001.png`;
        firstImg.onload = () => {
            frames[0] = firstImg;
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            updateMaxScroll();
            initialized = true;
            updateImage(window.scrollY);
            canvas.style.opacity = '0.4'; // Subtle fade-in
        };

        // Lazy load the rest in the background after the page has fully loaded
        window.addEventListener('load', () => {
            const loadFrames = () => {
                let currentFrame = 2;
                const loadNext = () => {
                    if (currentFrame > frameCount) return;
                    const img = new Image();
                    const frameNum = currentFrame.toString().padStart(3, '0');
                    img.src = `/frames/ezgif-frame-${frameNum}.png`;
                    frames[currentFrame - 1] = img;
                    currentFrame++;
                    // stagger loading to avoid network blocking
                    setTimeout(loadNext, 15);
                };
                loadNext();
            };
            
            if ('requestIdleCallback' in window) {
                requestIdleCallback(loadFrames);
            } else {
                setTimeout(loadFrames, 1000);
            }
        });

        window.addEventListener('resize', () => {
            if (!initialized) return;
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            updateMaxScroll();
            updateImage(window.scrollY);
        });

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
    }

    // ---- Form Submission Logic ----
    const form = document.getElementById('predict-form');
    const resultDisplayContainer = document.getElementById('result-display-container');
    const resultDisplay = document.getElementById('result-display');
    const submitBtn = form.querySelector('.submit-btn');

    // Make sliders interactive by filling the track
    const updateSlider = (el) => {
        const val = el.value;
        const percentage = (val / 10) * 100;
        // Updated minimal accent fill
        el.style.background = `linear-gradient(to right, #0f172a 0%, #0f172a ${percentage}%, #e2e8f0 ${percentage}%, #e2e8f0 100%)`;
        
        // Update textual label
        let labelText = "Average";
        if (val >= 9) labelText = "Like New";
        else if (val >= 7) labelText = "Good";
        else if (val >= 4) labelText = "Average";
        else labelText = "Needs Repair";
        
        const textElement = el.parentElement.querySelector('.condition-text');
        if (textElement) textElement.innerText = labelText;
    };

    document.querySelectorAll('input[type="range"]').forEach(slider => {
        // Initial call
        updateSlider(slider);
        
        slider.addEventListener('input', (e) => {
            updateSlider(e.target);
            const valDisplay = document.getElementById(`val-${e.target.name}`);
            if (valDisplay) valDisplay.innerText = e.target.value;
        });
    });

    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            setTimeout(() => {
                document.querySelectorAll('input[type="range"]').forEach(slider => {
                    updateSlider(slider);
                    const valDisplay = document.getElementById(`val-${slider.name}`);
                    if (valDisplay) valDisplay.innerText = slider.value;
                });
                resultDisplayContainer.classList.add('hidden');
                updateMaxScroll();
                
                const variantSelect = document.getElementById('model_variant');
                if (variantSelect) {
                    variantSelect.innerHTML = '<option disabled selected value="">Select Brand First</option>';
                    variantSelect.disabled = true;
                }
                
                // Scroll back up to the top of the form
                document.getElementById('predict-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 10);
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Loading state
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="flex items-center justify-center gap-2"><span class="w-4 h-4 border-2 border-surface border-t-transparent rounded-full animate-spin"></span> Processing...</span>';
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
            const response = await fetch(`${API_BASE}/api/predict`, {
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
                featuresHTML = '<div class="mt-6 text-sm text-left bg-background p-4 rounded-xl border border-border">';
                featuresHTML += '<div class="font-semibold mb-3 text-ink-muted text-xs uppercase tracking-wider">Factors considered in this estimate</div>';
                featuresHTML += '<div class="flex flex-col gap-3">';
                for (const [feat, val] of topFeatures) {
                    const percentage = (val * 100).toFixed(1);
                    const cleanFeat = feat.replace('num__', '').replace('cat__', '').replace('remainder__', '').replace(/_/g, ' ');
                    featuresHTML += `
                        <div class="flex flex-col gap-1">
                            <div class="flex justify-between capitalize text-ink text-xs font-medium">
                                <span>${cleanFeat}</span>
                                <span class="text-ink-muted">${percentage}% impact</span>
                            </div>
                            <div class="w-full bg-border rounded-full h-1.5">
                                <div class="bg-accent h-1.5 rounded-full" style="width: ${percentage}%"></div>
                            </div>
                        </div>
                    `;
                }
                featuresHTML += '</div></div>';
            }

            // Render Result
            resultDisplayContainer.classList.remove('hidden');
            setTimeout(updateMaxScroll, 50);
            
            resultDisplay.innerHTML = `
                <div class="text-center">
                    <div class="text-ink-muted uppercase tracking-wider text-xs font-semibold mb-2">Estimated Market Value</div>
                    <div class="text-5xl font-bold text-ink tracking-tight mb-2">${formattedPrice}</div>
                    <p class="text-ink-muted text-sm font-medium">
                        Estimated Market Range: ${formatCI(data.confidence_interval[0])} - ${formatCI(data.confidence_interval[1])}
                    </p>
                    ${featuresHTML}
                </div>
            `;

            // Smooth scroll to results
            resultDisplayContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        } catch (err) {
            resultDisplayContainer.classList.remove('hidden');
            setTimeout(updateMaxScroll, 50);
            resultDisplay.innerHTML = `
                <div class="text-center text-red-600 p-4 bg-red-50 rounded-xl border border-red-200">
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
