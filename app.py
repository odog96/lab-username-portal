from flask import Flask, request, jsonify, render_template_string, send_from_directory
import json
import os

app = Flask(__name__)

# Configuration file
CONFIG_FILE = 'lab_config.json'
ASSIGNMENTS_FILE = 'lab_assignments.json'

def load_config():
    """Load lab configuration"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Add default values for password and url if they don't exist
            if 'password' not in config:
                config['password'] = ''
            if 'url' not in config:
                config['url'] = ''
            return config
    return {
        'max_users': 0,
        'lab_name': 'Hands-On Lab',
        'password': '',
        'url': ''
    }

def save_config(config):
    """Save lab configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_assignments():
    """Load user assignments"""
    if os.path.exists(ASSIGNMENTS_FILE):
        with open(ASSIGNMENTS_FILE, 'r') as f:
            return json.load(f)
    return {
        'email_to_user': {},
        'assigned_users': []
    }

def save_assignments(assignments):
    """Save user assignments"""
    with open(ASSIGNMENTS_FILE, 'w') as f:
        json.dump(assignments, f, indent=2)

@app.route('/')
def index():
    config = load_config()
    if config['max_users'] == 0:
        return render_template_string(SETUP_REQUIRED_HTML)
    return render_template_string(USER_HTML, lab_name=config['lab_name'])

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML)

@app.route('/download/readme')
def download_readme():
    """Serve the lab README PDF"""
    try:
        return send_from_directory('/home/cdsw', 'lab-readme.pdf', as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current lab configuration"""
    config = load_config()
    assignments = load_assignments()
    return jsonify({
        'max_users': config['max_users'],
        'lab_name': config['lab_name'],
        'password': config['password'],
        'url': config['url'],
        'total_assigned': len(assignments['email_to_user']),
        'slots_remaining': config['max_users'] - len(assignments['email_to_user'])
    })

@app.route('/api/config', methods=['POST'])
def set_config():
    """Set lab configuration (max users)"""
    data = request.json
    max_users = data.get('max_users', 0)
    lab_name = data.get('lab_name', 'Hands-On Lab')
    password = data.get('password', '')
    url = data.get('url', '')

    if max_users <= 0:
        return jsonify({'error': 'max_users must be greater than 0'}), 400

    config = {
        'max_users': max_users,
        'lab_name': lab_name,
        'password': password,
        'url': url
    }
    save_config(config)

    return jsonify({'message': f'Lab configured for {max_users} users', 'config': config})

@app.route('/api/request-username', methods=['POST'])
def request_username():
    """Request a username for an email"""
    data = request.json
    email = data.get('email', '').lower().strip()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Load config and assignments
    config = load_config()
    if config['max_users'] == 0:
        return jsonify({'error': 'Lab not configured. Please contact administrator.'}), 400
    
    assignments = load_assignments()
    
    # Check if email already has an assignment
    if email in assignments['email_to_user']:
        user_num = assignments['email_to_user'][email]
        return jsonify({
            'already_assigned': True,
            'user_number': user_num,
            'username': f"user{str(user_num).zfill(3)}",
            'password': config['password'],
            'url': config['url'],
            'message': 'You have already been assigned a username.'
        })
    
    # Check if we have slots available
    if len(assignments['email_to_user']) >= config['max_users']:
        return jsonify({'error': f'All {config["max_users"]} slots have been assigned.'}), 400
    
    # Find next available user number
    next_user = 1
    while next_user in assignments['assigned_users']:
        next_user += 1
    
    # Assign user number
    assignments['email_to_user'][email] = next_user
    assignments['assigned_users'].append(next_user)
    assignments['assigned_users'].sort()
    
    # Save assignments
    save_assignments(assignments)
    
    return jsonify({
        'already_assigned': False,
        'user_number': next_user,
        'username': f"user{str(next_user).zfill(3)}",
        'password': config['password'],
        'url': config['url'],
        'total_assigned': len(assignments['email_to_user']),
        'slots_remaining': config['max_users'] - len(assignments['email_to_user'])
    })

@app.route('/api/admin/assignments', methods=['GET'])
def get_assignments():
    """Get all assignments"""
    config = load_config()
    assignments = load_assignments()
    
    # Build list of assignments with details
    assignment_list = []
    for email, user_num in assignments['email_to_user'].items():
        assignment_list.append({
            'email': email,
            'user_number': user_num,
            'username': f"user{str(user_num).zfill(3)}"
        })
    
    # Sort by user number
    assignment_list.sort(key=lambda x: x['user_number'])
    
    return jsonify({
        'config': config,
        'total_assigned': len(assignments['email_to_user']),
        'slots_remaining': config['max_users'] - len(assignments['email_to_user']),
        'assignments': assignment_list
    })

@app.route('/api/admin/reset', methods=['POST'])
def reset_assignments():
    """Reset everything - config and assignments"""
    if os.path.exists(ASSIGNMENTS_FILE):
        os.remove(ASSIGNMENTS_FILE)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    return jsonify({'message': 'All data has been reset. Please reconfigure the lab.'})

@app.route('/api/admin/reset-all', methods=['POST'])
def reset_all():
    """Reset everything including config"""
    if os.path.exists(ASSIGNMENTS_FILE):
        os.remove(ASSIGNMENTS_FILE)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    return jsonify({'message': 'All data has been reset.'})

# HTML Templates
SETUP_REQUIRED_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lab Setup Required</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
            text-align: center;
        }
        h1 { color: #2d3748; margin-bottom: 20px; }
        p { color: #718096; margin-bottom: 30px; }
        .btn {
            padding: 14px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Lab Not Configured</h1>
        <p>This lab has not been set up yet. Please configure the number of users before participants can register.</p>
        <a href="/admin" class="btn">Go to Admin Setup</a>
    </div>
</body>
</html>
'''

USER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ lab_name }} - Get Username</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 28px;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #718096;
            font-size: 14px;
        }
        
        .download-link {
            display: inline-block;
            margin-top: 12px;
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }
        
        .download-link:hover {
            text-decoration: underline;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #4a5568;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        input[type="email"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="email"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .result {
            display: none;
            margin-top: 30px;
            padding: 30px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            text-align: center;
        }
        
        .result.show {
            display: block;
            animation: fadeIn 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .result h2 {
            color: #2d3748;
            font-size: 24px;
            margin-bottom: 15px;
        }
        
        .username-display {
            display: inline-block;
            padding: 15px 30px;
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }
        
        .result p {
            color: #718096;
            margin-top: 15px;
        }
        
        .already-assigned {
            background: #fff5f5;
            border-left-color: #f59e0b;
        }
        
        .error {
            display: none;
            margin-top: 15px;
            padding: 12px 16px;
            background: #fff5f5;
            border-left: 4px solid #f56565;
            border-radius: 8px;
            color: #c53030;
            font-size: 14px;
        }
        
        .error.show {
            display: block;
            animation: fadeIn 0.5s;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {{ lab_name }}</h1>
            <p>Enter your email to get your username</p>
            <a href="/download/readme" class="download-link">📄 Download Lab Instructions (PDF)</a>
        </div>
        
        <form id="usernameForm">
            <div class="input-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" placeholder="your.email@company.com" required>
            </div>
            <button type="submit" class="btn">Get My Username</button>
        </form>
        
        <div id="error" class="error"></div>
        
        <div id="result" class="result">
            <h2 id="resultTitle">You are:</h2>
            <div class="username-display" id="username"></div>
            <div style="margin-top: 20px;">
                <div style="margin-bottom: 15px;">
                    <strong style="color: #4a5568;">Password:</strong>
                    <div style="display: inline-block; padding: 8px 16px; background: white; border: 2px solid #667eea; border-radius: 6px; font-family: 'Courier New', monospace; font-weight: bold; color: #667eea; margin-left: 10px;" id="password"></div>
                </div>
                <div style="margin-bottom: 15px;">
                    <strong style="color: #4a5568;">Lab URL:</strong>
                    <div style="display: inline-block; padding: 8px 16px; background: white; border: 2px solid #667eea; border-radius: 6px; margin-left: 10px;">
                        <a id="labUrl" href="#" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 600;">Click here to access lab</a>
                    </div>
                </div>
            </div>
            <p id="resultMessage"></p>
        </div>
    </div>

    <script>
        document.getElementById('usernameForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value.toLowerCase().trim();
            const errorDiv = document.getElementById('error');
            const resultDiv = document.getElementById('result');
            const submitBtn = this.querySelector('button[type="submit"]');
            
            errorDiv.classList.remove('show');
            resultDiv.classList.remove('show');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            
            fetch('/api/request-username', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to get username');
                    });
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('username').textContent = data.username;
                document.getElementById('password').textContent = data.password || 'Not set';

                const labUrlElement = document.getElementById('labUrl');
                if (data.url) {
                    labUrlElement.href = data.url;
                    labUrlElement.textContent = data.url;
                } else {
                    labUrlElement.href = '#';
                    labUrlElement.textContent = 'Not set';
                }

                if (data.already_assigned) {
                    document.getElementById('resultTitle').textContent = 'You already have a username:';
                    document.getElementById('resultMessage').textContent = 'You previously registered with this email address.';
                    resultDiv.classList.add('already-assigned');
                } else {
                    document.getElementById('resultTitle').textContent = 'You are:';
                    document.getElementById('resultMessage').textContent = `Successfully assigned! ${data.slots_remaining} slots remaining.`;
                    resultDiv.classList.remove('already-assigned');
                }

                resultDiv.classList.add('show');
            })
            .catch(error => {
                errorDiv.textContent = error.message;
                errorDiv.classList.add('show');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Get My Username';
            });
        });
    </script>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Lab Setup</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f7fafc;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .header h1 { color: #2d3748; margin-bottom: 10px; }
        
        .setup-section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #4a5568;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .form-group input {
            width: 100%;
            max-width: 400px;
            padding: 10px 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin-right: 10px;
            font-size: 14px;
        }
        
        .btn:hover { background: #5a67d8; }
        .btn-danger { background: #f56565; }
        .btn-danger:hover { background: #e53e3e; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: #718096;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        
        .stat-card .value {
            color: #2d3748;
            font-size: 32px;
            font-weight: bold;
        }
        
        .assignments-section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        th {
            background: #f7fafc;
            color: #4a5568;
            font-weight: 600;
            font-size: 14px;
        }
        
        .message {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .message.show { display: block; }
        .message.success { background: #c6f6d5; color: #22543d; }
        .message.error { background: #fed7d7; color: #742a2a; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ Lab Setup & Administration</h1>
            <p>Configure your hands-on lab and manage user assignments</p>
        </div>
        
        <div id="message" class="message"></div>
        
        <div class="setup-section">
            <h2 style="margin-bottom: 20px;">Lab Configuration</h2>
            <form id="configForm">
                <div class="form-group">
                    <label for="labName">Lab Name</label>
                    <input type="text" id="labName" placeholder="e.g., AI Workshop 2024" required>
                </div>
                <div class="form-group">
                    <label for="maxUsers">Maximum Number of Users</label>
                    <input type="number" id="maxUsers" min="1" placeholder="e.g., 150" required>
                </div>
                <div class="form-group">
                    <label for="password">Password (same for all users)</label>
                    <input type="text" id="password" placeholder="e.g., Lab2024!">
                </div>
                <div class="form-group">
                    <label for="url">URL to Access Lab (same for all users)</label>
                    <input type="url" id="url" placeholder="e.g., https://lab.example.com">
                </div>
                <button type="submit" class="btn">💾 Save Configuration</button>
            </form>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Max Users</h3>
                <div class="value" id="maxUsersDisplay">-</div>
            </div>
            <div class="stat-card">
                <h3>Assigned</h3>
                <div class="value" id="assignedDisplay">-</div>
            </div>
            <div class="stat-card">
                <h3>Remaining</h3>
                <div class="value" id="remainingDisplay">-</div>
            </div>
        </div>
        
        <div class="assignments-section">
            <h2>User Assignments</h2>
            <div style="margin: 20px 0;">
                <button class="btn" onclick="loadAssignments()">🔄 Refresh</button>
                <button class="btn btn-danger" onclick="resetAssignments()">⚠️ Reset Everything</button>
            </div>
            <div id="assignmentsTable"></div>
        </div>
    </div>

    <script>
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = `message show ${type}`;
            setTimeout(() => msg.classList.remove('show'), 5000);
        }
        
        function loadConfig() {
            fetch('/api/config')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('maxUsersDisplay').textContent = data.max_users;
                    document.getElementById('assignedDisplay').textContent = data.total_assigned;
                    document.getElementById('remainingDisplay').textContent = data.slots_remaining;
                });
        }
        
        function loadAssignments() {
            fetch('/api/admin/assignments')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('maxUsersDisplay').textContent = data.config.max_users;
                    document.getElementById('assignedDisplay').textContent = data.total_assigned;
                    document.getElementById('remainingDisplay').textContent = data.slots_remaining;

                    // Populate form fields
                    document.getElementById('labName').value = data.config.lab_name || '';
                    document.getElementById('maxUsers').value = data.config.max_users || '';
                    document.getElementById('password').value = data.config.password || '';
                    document.getElementById('url').value = data.config.url || '';

                    let html = '<table><thead><tr><th>User #</th><th>Username</th><th>Email</th></tr></thead><tbody>';

                    if (data.assignments.length === 0) {
                        html = '<p style="color: #718096; padding: 20px; text-align: center;">No assignments yet</p>';
                    } else {
                        data.assignments.forEach(a => {
                            html += `<tr><td>${a.user_number}</td><td>${a.username}</td><td>${a.email}</td></tr>`;
                        });
                        html += '</tbody></table>';
                    }

                    document.getElementById('assignmentsTable').innerHTML = html;
                });
        }
        
        document.getElementById('configForm').addEventListener('submit', function(e) {
            e.preventDefault();

            const config = {
                lab_name: document.getElementById('labName').value,
                max_users: parseInt(document.getElementById('maxUsers').value),
                password: document.getElementById('password').value,
                url: document.getElementById('url').value
            };

            fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            })
            .then(r => r.json())
            .then(data => {
                showMessage(data.message, 'success');
                loadConfig();
                loadAssignments();
            })
            .catch(err => {
                showMessage('Error saving configuration', 'error');
            });
        });
        
        function resetAssignments() {
            if (!confirm('Reset EVERYTHING (config + assignments)? You will need to reconfigure the lab.')) return;
            
            fetch('/api/admin/reset', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    showMessage(data.message, 'success');
                    document.getElementById('labName').value = '';
                    document.getElementById('maxUsers').value = '';
                    loadConfig();
                    loadAssignments();
                });
        }
        
        // Load data on page load
        loadConfig();
        loadAssignments();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            loadConfig();
            loadAssignments();
        }, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=int(os.environ["CDSW_READONLY_PORT"]))