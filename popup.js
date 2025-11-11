let isAnalyzing = false;

const elements = {
    mainButton: document.getElementById('mainButton'),
    buttonIcon: document.getElementById('buttonIcon'),
    buttonText: document.getElementById('buttonText'),
    status: document.getElementById('status'),
    statusText: document.getElementById('statusText'),
    debugText: document.getElementById('debugText'),
    error: document.getElementById('error'),
    result: document.getElementById('result')
};

function showStatus(status, debug = '') {
    elements.status.classList.add('show');
    elements.statusText.textContent = status;
    elements.debugText.textContent = debug;
}

function hideStatus() {
    elements.status.classList.remove('show');
}

function showError(error) {
    elements.error.textContent = error;
    elements.error.classList.add('show');
}

function hideError() {
    elements.error.classList.remove('show');
}

function showResult(result) {
    elements.result.classList.add('show');
    document.getElementById('resultType').textContent = result.type;
    document.getElementById('resultTitle').textContent = result.title;
    
    const detailsContainer = document.getElementById('detailsContainer');
    if (result.details) {
        detailsContainer.style.display = 'block';
        document.getElementById('resultDetails').textContent = result.details;
    } else {
        detailsContainer.style.display = 'none';
    }
    
    const badge = document.getElementById('confidenceBadge');
    badge.textContent = result.confidence + ' confidence';
    badge.className = 'confidence-badge confidence-' + result.confidence;
}

function hideResult() {
    elements.result.classList.remove('show');
}

function updateButton(analyzing) {
    if (analyzing) {
        elements.mainButton.classList.add('analyzing');
        elements.buttonIcon.classList.add('spin');
        elements.buttonText.textContent = 'Analyzing...';
    } else {
        elements.mainButton.classList.remove('analyzing');
        elements.buttonIcon.classList.remove('spin');
        elements.buttonText.textContent = 'Tap to Identify';
    }
}

async function captureAndAnalyze() {
    if (isAnalyzing) return;
    
    isAnalyzing = true;
    updateButton(true);
    hideError();
    hideResult();
    
    try {
        showStatus('Requesting screen access...');
        
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { width: { ideal: 1920 }, height: { ideal: 1080 } },
            audio: false
        });

        showStatus('Capturing video...', 'Setting up capture');
        
        const video = document.createElement('video');
        video.srcObject = stream;
        await video.play();

        showStatus('Waiting for stable frames...', 'Please wait 5 seconds');
        await new Promise(resolve => setTimeout(resolve, 5000));

        const frames = [];
        for (let i = 0; i < 2; i++) {
            showStatus('Capturing frames...', `Frame ${i + 1}/2`);
            
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
            frames.push(dataUrl.split(',')[1]);
            
            if (i < 1) await new Promise(resolve => setTimeout(resolve, 1500));
        }

        stream.getTracks().forEach(track => track.stop());

        if (frames.length === 0) {
            throw new Error('Could not capture frames');
        }

        showStatus('Analyzing with AI...', 'Sending to Claude');

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'claude-sonnet-4-20250514',
                max_tokens: 1500,
                messages: [{
                    role: 'user',
                    content: [
                        {
                            type: 'image',
                            source: { type: 'base64', media_type: 'image/jpeg', data: frames[0] }
                        },
                        {
                            type: 'text',
                            text: `Analyze this screenshot and identify what the user is watching. Look for movie/TV titles, YouTube videos, sports games, or any visible content.

Respond in this exact JSON format (no markdown):
{
  "identified": true,
  "type": "movie/tv/youtube/sports/other",
  "title": "exact title",
  "details": "additional info",
  "confidence": "high/medium/low"
}`
                        }
                    ]
                }]
            })
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const data = await response.json();
        const text = data.content.find(c => c.type === 'text')?.text || '';
        
        let result;
        try {
            const clean = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
            result = JSON.parse(clean);
        } catch {
            result = {
                identified: true,
                type: 'content',
                title: 'Content Detected',
                details: text.substring(0, 150),
                confidence: 'low'
            };
        }

        showResult(result);
        showStatus('Complete!', 'Success');

    } catch (err) {
        console.error('Error:', err);
        showError('Failed: ' + err.message);
    } finally {
        isAnalyzing = false;
        updateButton(false);
    }
}

elements.mainButton.addEventListener('click', captureAndAnalyze);