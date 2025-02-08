const video = document.getElementById('video');
const captureButton = document.getElementById('capture');
const resultDiv = document.getElementById('result');

// Start the video feed
navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    .then(stream => video.srcObject = stream)
    .catch(err => console.error('Camera access denied:', err));

// Capture frame on button click
captureButton.addEventListener('click', async () => {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

    const frameData = canvas.toDataURL('image/jpeg');
    try {
        const response = await fetch('/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ frame: frameData })
        });

        const result = await response.json();
        if (result.status === 'success') {
            resultDiv.innerHTML = `
                <p>Roll Number: ${result.qr_code}</p>
                <p>Name: ${result.name}</p>
            `;
        } else if (result.status === 'failure') {
            resultDiv.innerHTML = `<p>Error: ${result.message}</p>`;
        } else {
            resultDiv.innerHTML = `<p>Unexpected Error: ${result.message}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p>Error: Unable to communicate with the server.</p>`;
        console.error('Error capturing frame:', error);
    }
});
