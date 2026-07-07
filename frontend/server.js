const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

app.use(express.json());

// Proxy socket.io requests to RASA
const apiProxy = createProxyMiddleware({
  pathFilter: '/socket.io',
  target: 'http://localhost:5005', 
  ws: true,
  changeOrigin: true
});

app.use(apiProxy);

// Endpoint to send booking email using Python SMTP utility
app.post('/api/send-booking-email', (req, res) => {
  const { email, name, age, vaccine, dose, timeSlot, refCode, hospitalName, hospitalAddress } = req.body;
  
  const exec = require('child_process').exec;
  const path = require('path');
  
  // Resolve paths to environment python and mailer script
  const pythonPath = path.join(__dirname, '..', 'env', 'Scripts', 'python.exe');
  const scriptPath = path.join(__dirname, '..', 'api', 'send_booking_email.py');
  
  const esc = (str) => (str || '').replace(/"/g, '\\"');
  
  const cmd = `"${pythonPath}" "${scriptPath}" ` +
    `--email "${esc(email)}" ` +
    `--name "${esc(name)}" ` +
    `--age "${esc(age)}" ` +
    `--vaccine "${esc(vaccine)}" ` +
    `--dose "${esc(dose)}" ` +
    `--slot "${esc(timeSlot)}" ` +
    `--ref "${esc(refCode)}" ` +
    `--hospital "${esc(hospitalName)}" ` +
    `--address "${esc(hospitalAddress)}"`;
    
  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      return res.status(500).json({ status: 'error', error: stderr || err.message });
    }
    const status = stdout.trim();
    if (status === 'success') {
      res.json({ status: 'success' });
    } else {
      res.json({ status: 'error', message: status });
    }
  });
});

// Serve static frontend files
app.use(express.static(__dirname));

const PORT = 3000;
const server = app.listen(PORT, () => {
  console.log(`Frontend & Proxy running on port ${PORT}`);
});

// CRITICAL: Proxy websockets by listening to the upgrade event
server.on('upgrade', apiProxy.upgrade);
