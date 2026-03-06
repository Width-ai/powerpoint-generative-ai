import base64
import io
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from groq import Groq
from flask import Flask, jsonify, render_template_string, request, send_file

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from transcription.prompts import INTAKE_CALL_EXTRACTION
from proposal_gen.prompts import CUSTOM_PROPOSAL_SECTION_PROMPT, USER_CUSTOM_PROPOSAL_SECTION_PROMPT

app = Flask(__name__)

print("=" * 50)
print("Environment Variables Check:")
print(f"N8N_WEBHOOK_URL: {os.environ.get('N8N_WEBHOOK_URL', 'NOT SET')}")
print(f"GROQ_API_KEY: {'SET' if os.environ.get('GROQ_API_KEY') else 'NOT SET'}")
print("=" * 50)


BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #f0f4ff 0%, #fdf2f8 100%);
    color: #1e293b;
    min-height: 100vh;
}

/* -- nav -- */
nav {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 20px;
    display: flex;
    justify-content: center;
    gap: 4px;
}
nav a {
    text-decoration: none;
    color: #64748b;
    font-weight: 600;
    font-size: 14px;
    padding: 14px 20px;
    border-bottom: 2px solid transparent;
    transition: all 0.15s ease;
}
nav a:hover { color: #6366f1; }
nav a.active {
    color: #6366f1;
    border-bottom-color: #6366f1;
}

.container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.header { text-align: center; margin-bottom: 36px; }
.header h1 {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.header p { color: #64748b; font-size: 15px; }

.card {
    background: #fff;
    padding: 32px;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    margin-bottom: 24px;
}

/* -- file upload -- */
.upload-area {
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 40px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 24px;
    background: #f8fafc;
}
.upload-area:hover, .upload-area.dragover {
    border-color: #818cf8;
    background: #eef2ff;
}
.upload-area.has-file {
    border-color: #6366f1;
    border-style: solid;
    background: #eef2ff;
}
.upload-area input[type="file"] { display: none; }
.upload-icon {
    width: 48px; height: 48px;
    margin: 0 auto 12px;
    background: #e0e7ff;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
}
.upload-icon svg { width: 24px; height: 24px; color: #6366f1; }
.upload-label { font-weight: 600; color: #334155; margin-bottom: 4px; }
.upload-hint { font-size: 13px; color: #94a3b8; }
.file-name { font-weight: 600; color: #6366f1; font-size: 15px; }

/* -- textarea -- */
textarea {
    width: 100%;
    min-height: 200px;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.6;
    color: #334155;
    resize: vertical;
    transition: border-color 0.2s ease;
    margin-bottom: 24px;
    background: #f8fafc;
}
textarea:focus {
    outline: none;
    border-color: #818cf8;
    background: #fff;
}
textarea::placeholder { color: #94a3b8; }
.field-label {
    display: block;
    font-weight: 600;
    font-size: 14px;
    color: #334155;
    margin-bottom: 8px;
}

/* -- button -- */
.btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    border: none;
    padding: 12px 32px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    width: 100%;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}
.btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(99,102,241,0.4); }
.btn:disabled { opacity: 0.6; cursor: wait; transform: none; box-shadow: none; }

/* -- spinner -- */
.spinner { display: none; }
form.loading .spinner { display: inline-block; }
form.loading .btn-label { display: none; }
@keyframes spin { to { transform: rotate(360deg); } }
.spinner-icon {
    width: 20px; height: 20px;
    border: 2.5px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
}

/* -- dual-button row (PPT + RTF) -- */
.btn-row { display: flex; gap: 12px; }
.btn-row .btn { flex: 1; }
.btn-rtf { background: linear-gradient(135deg, #f59e0b, #d97706); }
.btn-rtf:hover { box-shadow: 0 4px 16px rgba(245,158,11,0.4); }
.btn.btn-loading .spinner { display: inline-block; }
.btn.btn-loading .btn-label { display: none; }

/* -- results -- */
.result h2 {
    font-size: 18px;
    font-weight: 700;
    color: #6366f1;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
}
.result pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    line-height: 1.7;
    font-family: inherit;
    font-size: 14px;
    color: #334155;
}

.error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
    padding: 16px 20px;
    border-radius: 12px;
    font-size: 14px;
}

/* -- ppt success banner -- */
.success-banner {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #166534;
    padding: 20px 24px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 24px;
}
.success-banner strong {
    display: block;
    margin-bottom: 8px;
    font-size: 16px;
}
"""

NAV = """
    <nav>
        <a href="/" {active_intake}>Intake Call Extraction</a>
        <a href="/picture-of-success" {active_pos}>Picture of Success</a>
        <a href="/ppt-generator" {active_ppt}>PPT Generator</a>
        <a href="/rtf-proposal" {active_rtf}>RTF Proposal</a>
    </nav>
"""

def make_nav(active):
    return NAV.format(
        active_intake='class="active"' if active == "intake" else "",
        active_pos='class="active"' if active == "pos" else "",
        active_ppt='class="active"' if active == "ppt" else "",
        active_rtf='class="active"' if active == "rtf" else "",
    )

INTAKE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Intake Call Extraction</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    {{ nav | safe }}
    <div class="container">
        <div class="header">
            <h1>Intake Call Extraction</h1>
            <p>Upload a transcript to extract goals, passions, struggles, and more.</p>
        </div>

        <form class="card" method="POST" enctype="multipart/form-data"
              onsubmit="this.classList.add('loading'); this.querySelector('.btn').disabled=true;">

            <div class="upload-area" id="dropZone" onclick="document.getElementById('transcript').click();">
                <input type="file" id="transcript" name="transcript" accept=".txt" required
                       onchange="handleFile(this)">
                <div class="upload-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
                    </svg>
                </div>
                <div class="upload-label" id="uploadLabel">Choose a file or drag it here</div>
                <div class="upload-hint" id="uploadHint">.txt files only</div>
            </div>

            <button type="submit" class="btn">
                <span class="btn-label">Extract Insights</span>
                <span class="spinner"><span class="spinner-icon"></span> Analyzing transcript...</span>
            </button>
        </form>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        {% if result %}
        <div class="card result">
            <h2>Extraction Result</h2>
            <pre>{{ result }}</pre>
        </div>
        {% endif %}
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('transcript');

        function handleFile(input) {
            if (input.files.length > 0) {
                const name = input.files[0].name;
                document.getElementById('uploadLabel').innerHTML = '<span class="file-name">' + name + '</span>';
                document.getElementById('uploadHint').textContent = 'Click to change file';
                dropZone.classList.add('has-file');
            }
        }

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', function() {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile(fileInput);
            }
        });
    </script>
</body>
</html>
"""


PICTURE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Picture of Success Generation</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    {{ nav | safe }}
    <div class="container">
        <div class="header">
            <h1>Picture of Success Generation</h1>
            <p>Paste the client's intake analysis to generate their transformation intention statement.</p>
        </div>

        <form class="card" method="POST"
              onsubmit="this.classList.add('loading'); this.querySelector('.btn').disabled=true;">
            <label class="field-label" for="intake_analysis">Client intake analysis</label>
            <textarea id="intake_analysis" name="intake_analysis" required
                      placeholder="Paste the client's intake call analysis here...">{{ intake_text or '' }}</textarea>

            <button type="submit" class="btn">
                <span class="btn-label">Generate Picture of Success</span>
                <span class="spinner"><span class="spinner-icon"></span> Generating...</span>
            </button>
        </form>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        {% if result %}
        <div class="card result">
            <h2>Picture of Success</h2>
            <pre>{{ result }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


PPT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PPT Generator</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    {{ nav | safe }}
    <div class="container">
        <div class="header">
            <h1>PPT Generator</h1>
            <p>Upload a proposal file to generate a branded PowerPoint presentation.</p>
        </div>

        <form class="card" id="pptForm" method="POST" enctype="multipart/form-data">

            <div class="upload-area" id="dropZone" onclick="document.getElementById('proposal').click();">
                <input type="file" id="proposal" name="proposal" accept=".md,.txt,.docx" required
                       onchange="handleFile(this)">
                <div class="upload-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
                    </svg>
                </div>
                <div class="upload-label" id="uploadLabel">Choose a file or drag it here</div>
                <div class="upload-hint" id="uploadHint">.md, .txt, or .docx proposal files</div>
            </div>

            <input type="hidden" id="actionType" name="action_type" value="ppt">
            <div class="btn-row">
                <button type="submit" class="btn" id="pptBtn"
                        onclick="setAction('ppt', this)">
                    <span class="btn-label">Generate PowerPoint</span>
                    <span class="spinner"><span class="spinner-icon"></span> Building deck...</span>
                </button>
                <button type="submit" class="btn btn-rtf" id="rtfBtn"
                        onclick="setAction('rtf', this)">
                    <span class="btn-label">Generate RTF</span>
                    <span class="spinner"><span class="spinner-icon"></span> Building document...</span>
                </button>
            </div>
        </form>

        <div id="errorMessage" class="error" style="display: none;"></div>
        <div id="successMessage" class="success-banner" style="display: none;"></div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('proposal');
        const form = document.getElementById('pptForm');
        const pptBtn = document.getElementById('pptBtn');
        const rtfBtn = document.getElementById('rtfBtn');
        const errorMsg = document.getElementById('errorMessage');
        const successMsg = document.getElementById('successMessage');

        let activeAction = 'ppt';
        let activeBtn = pptBtn;

        function setAction(type, btn) {
            activeAction = type;
            activeBtn = btn;
        }

        function handleFile(input) {
            if (input.files.length > 0) {
                const name = input.files[0].name;
                document.getElementById('uploadLabel').innerHTML = '<span class="file-name">' + name + '</span>';
                document.getElementById('uploadHint').textContent = 'Click to change file';
                dropZone.classList.add('has-file');
            }
        }

        function resetForm() {
            pptBtn.classList.remove('btn-loading');
            rtfBtn.classList.remove('btn-loading');
            pptBtn.disabled = false;
            rtfBtn.disabled = false;
            fileInput.value = '';
            document.getElementById('uploadLabel').textContent = 'Choose a file or drag it here';
            document.getElementById('uploadHint').textContent = '.md, .txt, or .docx proposal files';
            dropZone.classList.remove('has-file');
        }

        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            errorMsg.style.display = 'none';
            successMsg.style.display = 'none';

            activeBtn.classList.add('btn-loading');
            pptBtn.disabled = true;
            rtfBtn.disabled = true;

            const formData = new FormData(form);
            formData.set('action_type', activeAction);

            try {
                const response = await fetch('/ppt-generator', {
                    method: 'POST',
                    body: formData
                });

                const ct = response.headers.get('content-type') || '';

                if (response.ok && (ct.includes('presentation') || ct.includes('rtf'))) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    const cd = response.headers.get('content-disposition') || '';
                    a.download = cd.split('filename=')[1]?.replace(/"/g, '') ||
                                 (activeAction === 'ppt' ? 'presentation.pptx' : 'proposal.rtf');
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                    successMsg.innerHTML = activeAction === 'ppt'
                        ? '<strong>&#x2705; Success!</strong> Your PowerPoint has been generated and downloaded.'
                        : '<strong>&#x2705; Success!</strong> Your RTF document has been generated and downloaded.';
                    successMsg.style.display = 'block';
                    resetForm();
                } else {
                    const text = await response.text();
                    errorMsg.textContent = 'Error: ' + (text || 'Failed to generate document');
                    errorMsg.style.display = 'block';
                    activeBtn.classList.remove('btn-loading');
                    pptBtn.disabled = false;
                    rtfBtn.disabled = false;
                }
            } catch (error) {
                errorMsg.textContent = 'Error: ' + error.message;
                errorMsg.style.display = 'block';
                activeBtn.classList.remove('btn-loading');
                pptBtn.disabled = false;
                rtfBtn.disabled = false;
            }
        });

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', function() {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile(fileInput);
            }
        });
    </script>
</body>
</html>
"""


RTF_PROPOSAL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>RTF Proposal Converter</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    {{ nav | safe }}
    <div class="container">
        <div class="header">
            <h1>RTF Proposal Converter</h1>
            <p>Upload a proposal file to convert it to RTF format while preserving content.</p>
        </div>

        <form class="card" id="rtfForm" method="POST" enctype="multipart/form-data">

            <div class="upload-area" id="dropZone" onclick="document.getElementById('proposal').click();">
                <input type="file" id="proposal" name="proposal" accept=".md,.txt,.docx" required
                       onchange="handleFile(this)">
                <div class="upload-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
                    </svg>
                </div>
                <div class="upload-label" id="uploadLabel">Choose a file or drag it here</div>
                <div class="upload-hint" id="uploadHint">.md, .txt, or .docx proposal files</div>
            </div>

            <button type="submit" class="btn" id="convertBtn">
                <span class="btn-label">Convert to RTF</span>
                <span class="spinner"><span class="spinner-icon"></span> Converting...</span>
            </button>
        </form>

        <div id="errorMessage" class="error" style="display: none;"></div>
        <div id="successMessage" class="success-banner" style="display: none;"></div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('proposal');
        const form = document.getElementById('rtfForm');
        const convertBtn = document.getElementById('convertBtn');
        const errorMsg = document.getElementById('errorMessage');
        const successMsg = document.getElementById('successMessage');

        function handleFile(input) {
            if (input.files.length > 0) {
                const name = input.files[0].name;
                document.getElementById('uploadLabel').innerHTML = '<span class="file-name">' + name + '</span>';
                document.getElementById('uploadHint').textContent = 'Click to change file';
                dropZone.classList.add('has-file');
            }
        }

        function resetForm() {
            convertBtn.classList.remove('btn-loading');
            convertBtn.disabled = false;
            fileInput.value = '';
            document.getElementById('uploadLabel').textContent = 'Choose a file or drag it here';
            document.getElementById('uploadHint').textContent = '.md, .txt, or .docx proposal files';
            dropZone.classList.remove('has-file');
        }

        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            errorMsg.style.display = 'none';
            successMsg.style.display = 'none';

            convertBtn.classList.add('btn-loading');
            convertBtn.disabled = true;

            const formData = new FormData(form);

            try {
                const response = await fetch('/rtf-proposal', {
                    method: 'POST',
                    body: formData
                });

                const ct = response.headers.get('content-type') || '';

                if (response.ok && ct.includes('rtf')) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    const cd = response.headers.get('content-disposition') || '';
                    a.download = cd.split('filename=')[1]?.replace(/"/g, '') || 'proposal.rtf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                    successMsg.innerHTML = '<strong>&#x2705; Success!</strong> Your RTF document has been generated and downloaded.';
                    successMsg.style.display = 'block';
                    resetForm();
                } else {
                    const text = await response.text();
                    errorMsg.textContent = 'Error: ' + (text || 'Failed to convert document');
                    errorMsg.style.display = 'block';
                    convertBtn.classList.remove('btn-loading');
                    convertBtn.disabled = false;
                }
            } catch (error) {
                errorMsg.textContent = 'Error: ' + error.message;
                errorMsg.style.display = 'block';
                convertBtn.classList.remove('btn-loading');
                convertBtn.disabled = false;
            }
        });

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', function() {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile(fileInput);
            }
        });
    </script>
</body>
</html>
"""



@app.route("/", methods=["GET", "POST"])
def intake():
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("transcript")
        if not file or not file.filename:
            error = "Please upload a transcript file."
        else:
            try:
                transcript_text = file.read().decode("utf-8")
                prompt = INTAKE_CALL_EXTRACTION.format(transcript=transcript_text)

                api_key = os.environ.get("GROQ_API_KEY")
                if not api_key:
                    error = "GROQ_API_KEY environment variable not set."
                else:
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                        temperature=0.7,
                    )
                    result = response.choices[0].message.content
                    
                    n8n_webhook_url = os.environ.get("N8N_UPLOAD_URL") or os.environ.get("N8N_WEBHOOK_URL")
                    print(f"DEBUG: Using webhook URL: {n8n_webhook_url}")
                    if n8n_webhook_url and result:
                        try:
                            client_name = os.path.splitext(file.filename)[0] if file.filename else "Unknown"
                            payload = {
                                "client_name": client_name,
                                "transcript_filename": file.filename,
                                "intake_analysis": result,
                                "raw_transcript": transcript_text,
                                "data_type": "intake_extraction",
                                "timestamp": __import__("datetime").datetime.now().isoformat(),
                                "source": "flask_app"
                            }
                            
                            response_n8n = requests.post(
                                n8n_webhook_url,
                                json=payload,
                                timeout=10
                            )
                            
                            if response_n8n.status_code == 200 or response_n8n.status_code == 201:
                                print(f"[SUCCESS] Successfully sent to n8n: Status {response_n8n.status_code}")
                            else:
                                print(f"[WARNING] n8n webhook returned status {response_n8n.status_code}")
                                print(f"  URL: {n8n_webhook_url}")
                                print(f"  Response: {response_n8n.text[:200]}")
                        except requests.exceptions.RequestException as n8n_error:
                            print(f"[WARNING] Failed to send to n8n: {n8n_error}")
                            print(f"  URL: {n8n_webhook_url}")
                            print(f"  Make sure the webhook is active in n8n")
                        except Exception as n8n_error:
                            print(f"[ERROR] Unexpected error sending to n8n: {n8n_error}")
                            import traceback
                            traceback.print_exc()
            except Exception as e:
                error = f"Error: {e}"

    return render_template_string(
        INTAKE_HTML, css=BASE_CSS, nav=make_nav("intake"), result=result, error=error
    )


@app.route("/picture-of-success", methods=["GET", "POST"])
def picture_of_success():
    result = None
    error = None
    intake_text = ""

    if request.method == "POST":
        intake_text = request.form.get("intake_analysis", "").strip()
        if not intake_text:
            error = "Please paste the client's intake analysis."
        else:
            try:
                user_prompt = USER_CUSTOM_PROPOSAL_SECTION_PROMPT.format(
                    intake_analysis=intake_text,
                )

                api_key = os.environ.get("GROQ_API_KEY")
                if not api_key:
                    error = "GROQ_API_KEY environment variable not set."
                else:
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": CUSTOM_PROPOSAL_SECTION_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                    max_tokens=4096,
                        temperature=0.7,
                    )
                    result = response.choices[0].message.content
                    
                    n8n_webhook_url = os.environ.get("N8N_UPLOAD_URL") or os.environ.get("N8N_WEBHOOK_URL")
                    if n8n_webhook_url and result:
                        try:
                            payload = {
                                "picture_of_success": result,
                                "intake_analysis_used": intake_text[:500],
                                "data_type": "picture_of_success",
                                "timestamp": __import__("datetime").datetime.now().isoformat(),
                                "source": "flask_app"
                            }
                            
                            response_n8n = requests.post(
                                n8n_webhook_url,
                                json=payload,
                                timeout=10
                            )
                            
                            if response_n8n.status_code == 200 or response_n8n.status_code == 201:
                                print(f"[SUCCESS] Successfully sent Picture of Success to n8n: Status {response_n8n.status_code}")
                            else:
                                print(f"[WARNING] n8n webhook returned status {response_n8n.status_code}")
                                print(f"  URL: {n8n_webhook_url}")
                        except requests.exceptions.RequestException as n8n_error:
                            print(f"[WARNING] Failed to send Picture of Success to n8n: {n8n_error}")
                            print(f"  URL: {n8n_webhook_url}")
                        except Exception as n8n_error:
                            print(f"[ERROR] Unexpected error sending Picture of Success to n8n: {n8n_error}")
            except Exception as e:
                error = f"Error: {e}"

    return render_template_string(
        PICTURE_HTML,
        css=BASE_CSS,
        nav=make_nav("pos"),
        result=result,
        error=error,
        intake_text=intake_text,
    )


@app.route("/ppt-generator", methods=["GET", "POST"])
def ppt_generator():
    error = None
    success = False

    if request.method == "POST":
        file = request.files.get("proposal")
        action_type = request.form.get("action_type", "ppt")
        if not file or not file.filename:
            error = "Please upload a proposal file."
        else:
            filename = file.filename.lower()
            if not (filename.endswith(".md") or filename.endswith(".txt") or filename.endswith(".docx")):
                error = "Only .md, .txt, and .docx files are supported."
            else:
                try:
                    from ppt_gen.docx_reader import parse_docx

                    api_key = os.environ.get("GROQ_API_KEY")
                    if not api_key:
                        return "GROQ_API_KEY environment variable not set.", 500

                    base = os.path.splitext(file.filename)[0]

                    if action_type == "rtf":
                        from ppt_gen.RTF.rtf_service import RTFService

                        service = RTFService(groq_api_key=api_key)

                        if filename.endswith(".docx"):
                            file.seek(0)
                            proposal = parse_docx(io.BytesIO(file.read()))
                            rtf_bytes = service.generate_from_proposal(proposal)
                        else:
                            file.seek(0)
                            markdown_text = file.read().decode("utf-8")
                            rtf_bytes = service.generate_from_markdown(markdown_text)

                        out_name = f"{base}_proposal.rtf"
                        return send_file(
                            io.BytesIO(rtf_bytes),
                            mimetype="application/rtf",
                            as_attachment=True,
                            download_name=out_name,
                        )
                    else:
                        from ppt_gen.ppt_service import PPTService

                        service = PPTService(groq_api_key=api_key)

                        if filename.endswith(".docx"):
                            file.seek(0)
                            proposal = parse_docx(io.BytesIO(file.read()))
                            pptx_bytes = service.generate_from_proposal(proposal)
                        else:
                            file.seek(0)
                            markdown_text = file.read().decode("utf-8")
                            pptx_bytes = service.generate_from_markdown(markdown_text)

                        out_name = f"{base}_presentation.pptx"
                        return send_file(
                            io.BytesIO(pptx_bytes),
                            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            as_attachment=True,
                            download_name=out_name,
                        )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return str(e), 500

    return render_template_string(
        PPT_HTML,
        css=BASE_CSS,
        nav=make_nav("ppt"),
        error=error,
        success=success,
    )


@app.route("/rtf-proposal", methods=["GET", "POST"])
def rtf_proposal():
    error = None
    success = False

    if request.method == "POST":
        file = request.files.get("proposal")
        if not file or not file.filename:
            error = "Please upload a proposal file."
        else:
            filename = file.filename.lower()
            if not (filename.endswith(".md") or filename.endswith(".txt") or filename.endswith(".docx")):
                error = "Only .md, .txt, and .docx files are supported."
            else:
                try:
                    from proposal_rtf.rtf_converter import convert_docx_to_rtf, convert_markdown_to_rtf, convert_text_to_rtf

                    base = os.path.splitext(file.filename)[0]
                    file.seek(0)

                    if filename.endswith(".docx"):
                        rtf_bytes = convert_docx_to_rtf(io.BytesIO(file.read()))
                    elif filename.endswith(".md"):
                        markdown_text = file.read().decode("utf-8")
                        rtf_bytes = convert_markdown_to_rtf(markdown_text)
                    else:
                        text_content = file.read().decode("utf-8")
                        rtf_bytes = convert_text_to_rtf(text_content)

                    out_name = f"{base}.rtf"
                    return send_file(
                        io.BytesIO(rtf_bytes),
                        mimetype="application/rtf",
                        as_attachment=True,
                        download_name=out_name,
                    )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return str(e), 500

    return render_template_string(
        RTF_PROPOSAL_HTML,
        css=BASE_CSS,
        nav=make_nav("rtf"),
        error=error,
        success=success,
    )


@app.route("/api/ppt-generator", methods=["POST"])
def api_ppt_generator():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        if "file_content" in data:
            file_content = base64.b64decode(data["file_content"])
            file_name = data.get("file_name", "proposal.docx")
            file_type = data.get("file_type", "").lower() or os.path.splitext(file_name)[1].lower()
            
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return jsonify({"success": False, "error": "GROQ_API_KEY environment variable not set"}), 500
            
            if file_type == ".docx" or file_name.lower().endswith(".docx"):
                from ppt_gen.ppt_service import PPTService
                from ppt_gen.docx_reader import parse_docx
                
                service = PPTService(groq_api_key=api_key)
                proposal = parse_docx(io.BytesIO(file_content))
                pptx_bytes = service.generate_from_proposal(proposal)
            else:
                from ppt_gen.ppt_service import PPTService
                
                markdown_text = file_content.decode("utf-8")
                service = PPTService(groq_api_key=api_key)
                pptx_bytes = service.generate_from_markdown(markdown_text)
        
        elif "file_text" in data:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return jsonify({"success": False, "error": "GROQ_API_KEY environment variable not set"}), 500
            
            from ppt_gen.ppt_service import PPTService
            
            markdown_text = data["file_text"]
            service = PPTService(groq_api_key=api_key)
            pptx_bytes = service.generate_from_markdown(markdown_text)
        
        else:
            return jsonify({"success": False, "error": "Either 'file_content' (base64) or 'file_text' required"}), 400
        
        pptx_base64 = base64.b64encode(pptx_bytes).decode("utf-8")
        
        return jsonify({
            "success": True,
            "pptx_base64": pptx_base64,
            "filename": data.get("file_name", "proposal_presentation.pptx").replace(".docx", "").replace(".md", "").replace(".txt", "") + "_presentation.pptx"
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
