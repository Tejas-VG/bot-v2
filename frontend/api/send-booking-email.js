const nodemailer = require('nodemailer');

module.exports = async (req, res) => {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ status: 'error', message: 'Method Not Allowed' });
  }

  const { email, name, age, vaccine, dose, timeSlot, refCode, hospitalName, hospitalAddress, message } = req.body || {};

  if (!email) {
    return res.status(400).json({ status: 'error', message: 'Missing recipient email' });
  }

  // Get credentials from environment variables
  const username = process.env.EMAIL_USER || 'innovateyourself2build@gmail.com';
  const password = process.env.EMAIL_PASS;

  if (!password) {
    return res.status(500).json({ 
      status: 'error', 
      message: 'Email credentials missing. Please set EMAIL_PASS environment variable in Vercel settings.' 
    });
  }

  try {
    // Create SMTP transporter
    const transporter = nodemailer.createTransport({
      host: 'smtp.gmail.com',
      port: 587,
      secure: false, // true for 465, false for other ports
      auth: {
        user: username,
        pass: password,
      },
    });

    let emailBody = '';
    let emailSubject = 'Vaccine Appointment Confirmed!';

    if (name) {
      // Generate QR Code URL
      const qrInfo = `MAYDEN SMARTHEALTH PVT LTD\n\nReference ID: ${refCode}\nPatient Name: ${name}\nAge: ${age}\nVaccine: ${vaccine} - ${dose}\nTime Slot: ${timeSlot}\nHospital: ${hospitalName}`;
      const qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + encodeURIComponent(qrInfo);

      emailBody = `Vaccine Appointment Confirmed!
Reference ID: ${refCode}

Appointment Details:
----------------------------------------------
Facility:      ${hospitalName}
Address:       ${hospitalAddress}
Beneficiary:   ${name} (${age} years)
Vaccine:       ${vaccine} - ${dose}
Time Slot:     ${timeSlot}
----------------------------------------------
QR Verification Link: ${qrUrl}

Please bring your registered Govt photo ID card to the clinic counter for verification.

Thank you for choosing MAYDEN SMARTHEALTH PVT LTD.`;
    } else {
      emailSubject = 'COVID-19 Vaccine Slot Availability';
      emailBody = message || 'Here is the vaccination slot information you requested.';
    }

    // Send mail
    await transporter.sendMail({
      from: `"MAYDEN SMARTHEALTH" <${username}>`,
      to: email,
      subject: emailSubject,
      text: emailBody,
    });

    return res.status(200).json({ status: 'success' });
  } catch (error) {
    console.error('Email error:', error);
    return res.status(500).json({ status: 'error', message: error.message });
  }
};
