document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Metadata for dropdowns
    let hierarchy = {};
    const API_BASE = import.meta.env.VITE_API_URL || '';
    
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
