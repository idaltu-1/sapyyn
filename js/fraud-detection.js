/**
 * Fraud Detection Client-Side Script
 * Generates device fingerprint for fraud prevention
 */

class FraudDetection {
    constructor() {
        this.fingerprint = null;
    }

    async generateDeviceFingerprint() {
        const components = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screenResolution: `${screen.width}x${screen.height}`,
            colorDepth: screen.colorDepth,
            pixelRatio: window.devicePixelRatio,
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory || 'unknown',
            connection: this.getConnectionInfo(),
            plugins: this.getPluginsList(),
            webgl: this.getWebGLInfo(),
            canvas: await this.getCanvasFingerprint(),
            fonts: this.getAvailableFonts(),
            audio: await this.getAudioFingerprint()
        };

        // Create a hash from all components
        const fingerprintString = JSON.stringify(components);
        this.fingerprint = await this.hashString(fingerprintString);
        
        return {
            fingerprint: this.fingerprint,
            components: components
        };
    }

    getConnectionInfo() {
        if (navigator.connection) {
            return {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            };
        }
        return 'unknown';
    }

    getPluginsList() {
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            plugins.push(navigator.plugins[i].name);
        }
        return plugins.sort();
    }

    getWebGLInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return 'not supported';

            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
                version: gl.getParameter(gl.VERSION)
            };
        } catch (e) {
            return 'error';
        }
    }

    async getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Draw some text and shapes to create a unique fingerprint
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('Sapyyn Fraud Detection 🔒', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Device Fingerprint', 4, 45);

            return canvas.toDataURL();
        } catch (e) {
            return 'error';
        }
    }

    getAvailableFonts() {
        const testFonts = [
            'Arial', 'Helvetica', 'Times', 'Times New Roman', 'Courier New',
            'Verdana', 'Georgia', 'Palatino', 'Garamond', 'Comic Sans MS',
            'Trebuchet MS', 'Arial Black', 'Impact'
        ];
        
        const availableFonts = [];
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';
        
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        // Default font measurement
        context.font = testSize + ' monospace';
        const defaultWidth = context.measureText(testString).width;
        
        for (const font of testFonts) {
            context.font = testSize + ' ' + font + ', monospace';
            if (context.measureText(testString).width !== defaultWidth) {
                availableFonts.push(font);
            }
        }
        
        return availableFonts;
    }

    async getAudioFingerprint() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const analyser = audioContext.createAnalyser();
            const gainNode = audioContext.createGain();
            
            oscillator.type = 'triangle';
            oscillator.frequency.setValueAtTime(10000, audioContext.currentTime);
            
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            
            oscillator.connect(analyser);
            analyser.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.start(0);
            
            const frequencyData = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(frequencyData);
            
            oscillator.stop();
            
            return Array.from(frequencyData).slice(0, 30).join(',');
        } catch (e) {
            return 'error';
        }
    }

    async hashString(str) {
        const encoder = new TextEncoder();
        const data = encoder.encode(str);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
}

// Global function to get device fingerprint
window.getFraudDetectionData = async function() {
    const detector = new FraudDetection();
    const data = await detector.generateDeviceFingerprint();
    
    return {
        deviceFingerprint: data.fingerprint,
        screenResolution: data.components.screenResolution,
        timezone: data.components.timezone,
        language: data.components.language,
        plugins: data.components.plugins.join(','),
        canvasFingerprint: data.components.canvas
    };
};

// Auto-attach to forms when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Attach to registration/login forms
    const forms = document.querySelectorAll('form[data-fraud-detection="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fraudData = await getFraudDetectionData();
            
            // Add fraud detection data to form
            Object.keys(fraudData).forEach(key => {
                let input = form.querySelector(`input[name="${key}"]`);
                if (!input) {
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    form.appendChild(input);
                }
                input.value = fraudData[key];
            });
            
            // Submit the form
            form.submit();
        });
    });
});