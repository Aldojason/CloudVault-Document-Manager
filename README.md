
# ☁️ CloudVault — Cloud-Based Document Manager

CloudVault is a secure cloud-based document management application that allows users to upload, store, search, download, and delete their documents using Amazon S3.

Built with Python Flask and AWS, CloudVault provides user authentication and individual document storage spaces.

## ✨ Features

- 🔐 User Registration and Login
- 🔒 Password Hashing for Secure Authentication
- ☁️ Cloud File Storage using Amazon S3
- 📤 Upload Documents
- 📥 Download Documents
- 🗑️ Delete Documents
- 🔎 Search Documents by Filename
- 👤 Individual User Storage Isolation
- 🛡️ CSRF Protection
- 📱 Responsive Web Interface

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Framework |
| Flask-SQLAlchemy | Database Integration |
| SQLite | User Data Storage |
| Boto3 | AWS SDK for Python |
| Amazon S3 | Cloud File Storage |
| HTML | Frontend Structure |
| CSS | Styling |
| JavaScript | Frontend Functionality |
| Git & GitHub | Version Control |

## 🏗️ Architecture

```text
User
  |
  v
CloudVault Web Interface
  |
  v
Flask Backend
  |
  +------ Authentication
  |          |
  |          v
  |       SQLite Database
  |
  +------ Document Operations
             |
             v
          Boto3 SDK
             |
             v
          Amazon S3
```

## 📂 Project Structure

```text
CloudVault/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── login.html
│   └── register.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── instance/
    └── cloudvault.db
```

The database and virtual environment are generated locally and are not committed to GitHub.

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/CloudVault.git
cd CloudVault
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS Credentials

Install and configure the AWS CLI.

```bash
aws configure
```

Provide your AWS access key, secret key, default region, and output format when prompted.

Never commit AWS credentials or share them publicly.

### 5. Configure the Application

In `app.py`, configure your own S3 bucket name:

```python
BUCKET_NAME = "YOUR_S3_BUCKET_NAME"
```

Set a secure Flask secret key in PowerShell:

```powershell
$env:SECRET_KEY = "YOUR_LONG_RANDOM_SECRET"
```

Ensure your AWS identity has the required permissions for the configured S3 bucket.

### 6. Run the Application

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

Register an account and start managing your documents!

## 🔐 Security

CloudVault includes:

- Password hashing using Werkzeug.
- Session-based authentication.
- CSRF protection using Flask-WTF.
- Private S3 bucket access.
- User-specific S3 object prefixes.
- Server-side document access checks.

**Note:** This project is a learning and portfolio project. Additional production security measures, deployment configuration, and persistent database infrastructure are needed before handling sensitive documents in a public production environment.

## 🚀 Future Improvements

- File preview functionality.
- Drag-and-drop uploads.
- Document categories and folders.
- Storage usage analytics.
- Password reset functionality.
- Production deployment.
- Advanced document sharing.

## 👨‍💻 Author

**Aldo Jason A**

Computer Science and Engineering Student

## 📄 License

This project is licensed under the MIT License.
