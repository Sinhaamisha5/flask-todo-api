# Complete CI/CD Learning Guide - Interview Revision Notes

## Table of Contents
1. [Overview](#overview)
2. [Phase 1: Application Development](#phase-1-application-development)
3. [Phase 2: Containerization with Docker](#phase-2-containerization-with-docker)
4. [Phase 3: CI with GitHub Actions](#phase-3-ci-with-github-actions)
5. [Phase 4: CI with Jenkins](#phase-4-ci-with-jenkins)
6. [Key Concepts](#key-concepts)
7. [Common Interview Questions](#common-interview-questions)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## Overview

### What You Built
A complete CI/CD pipeline for a Python Flask REST API that automatically:
- Runs tests on every code push
- Builds Docker images
- Pushes to DockerHub
- Uses both GitHub Actions and Jenkins

### Tech Stack
- **Application:** Python Flask, SQLite
- **Containerization:** Docker
- **CI/CD:** GitHub Actions, Jenkins
- **Cloud:** AWS EC2
- **Registry:** DockerHub

---

## Phase 1: Application Development

### 1.1 Project Structure
```
flask-todo-api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container image definition
├── Jenkinsfile        # Jenkins pipeline definition
├── .gitignore         # Files to exclude from Git
├── README.md          # Documentation
├── .github/
│   └── workflows/
│       └── ci.yml     # GitHub Actions workflow
└── tests/
    ├── __init__.py
    └── test_app.py    # Unit tests
```

### 1.2 Setup EC2 Environment
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and tools
sudo apt install python3 python3-pip python3-venv -y

# Install curl for testing API
sudo apt install curl -y

# Install Git
sudo apt install git -y
```

### 1.3 Create Virtual Environment
```bash
# Create project directory
mkdir flask-todo-api
cd flask-todo-api

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**Why Virtual Environment?**
- Isolates project dependencies
- Prevents conflicts with system Python
- Makes environment reproducible
- Essential for Docker (you'll understand dependencies)

### 1.4 Dependencies (requirements.txt)
```txt
Flask==3.0.0
flask-cors==4.0.0
pytest==7.4.3
pytest-cov==4.1.0
```

**What Each Does:**
- `Flask` - Web framework for REST API
- `flask-cors` - Enables cross-origin requests (for frontends)
- `pytest` - Testing framework
- `pytest-cov` - Code coverage reporting

### 1.5 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.6 Flask Application (app.py) - Key Components

#### Imports
```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
```

#### App Initialization
```python
app = Flask(__name__)
CORS(app)
DATABASE = 'todos.db'
```

#### Database Functions
```python
def get_db():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Returns dicts instead of tuples
    return conn

def init_db():
    """Initialize database with todos table"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on startup
with app.app_context():
    init_db()
```

#### API Endpoints
```python
# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Get all todos
@app.route('/api/todos', methods=['GET'])
def get_todos():
    conn = get_db()
    todos = conn.execute('SELECT * FROM todos').fetchall()
    conn.close()
    return jsonify([dict(todo) for todo in todos]), 200

# Create todo
@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO todos (title, description) VALUES (?, ?)',
        (data['title'], data.get('description', ''))
    )
    conn.commit()
    todo_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': todo_id, 'message': 'Created'}), 201

# Update, Delete endpoints similar...
```

#### Run Application
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
```

### 1.7 Run Locally
```bash
# Start application
python app.py

# Test (in another terminal)
curl http://localhost:5000/health
curl http://localhost:5000/api/todos
curl -X POST http://localhost:5000/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn DevOps", "description": "Master CI/CD"}'
```

### 1.8 Unit Tests (tests/test_app.py)
```python
import pytest
import json
from app import app, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200

def test_create_todo(client):
    response = client.post('/api/todos',
                          data=json.dumps({'title': 'Test'}),
                          content_type='application/json')
    assert response.status_code == 201

# More tests...
```

### 1.9 Run Tests
```bash
pytest -v
pytest --cov=app tests/
```

---

## Phase 2: Containerization with Docker

### 2.1 Install Docker on EC2
```bash
# Install Docker
sudo apt update
sudo apt install docker.io -y

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version

# Add user to docker group
sudo usermod -aG docker ubuntu
sudo usermod -aG docker jenkins

# Logout and login again for group changes
exit
# SSH back in
```

### 2.2 Dockerfile - Line by Line
```dockerfile
# Base image - starts with Python pre-installed
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Document that container listens on port 5000
EXPOSE 5000

# Command to run when container starts
CMD ["python", "app.py"]
```

**Key Dockerfile Concepts:**
- `FROM` - Base image (like a template)
- `WORKDIR` - Sets working directory
- `COPY` - Copy files from host to container
- `RUN` - Execute commands during build
- `EXPOSE` - Document which port is used
- `CMD` - Default command when container runs

**Why Copy requirements.txt First?**
- Docker uses layer caching
- If requirements don't change, Docker reuses cached layer
- Speeds up builds significantly

### 2.3 .dockerignore
```
venv/
__pycache__/
*.pyc
*.db
.git/
.pytest_cache/
```

**Purpose:** Tells Docker what NOT to copy into image

### 2.4 Build Docker Image
```bash
# Build image
docker build -t flask-todo-api:v1 .

# Explanation:
# docker build - Build command
# -t flask-todo-api:v1 - Tag (name:version)
# . - Build context (current directory)

# List images
docker images
```

### 2.5 Run Docker Container
```bash
# Run container
docker run -d -p 5000:5000 --name todo-api flask-todo-api:v1

# Explanation:
# -d - Detached mode (background)
# -p 5000:5000 - Port mapping (host:container)
# --name todo-api - Container name
# flask-todo-api:v1 - Image to run

# Check running containers
docker ps

# View logs
docker logs todo-api

# Stop container
docker stop todo-api

# Remove container
docker rm todo-api
```

### 2.6 Push to DockerHub
```bash
# Login to DockerHub
docker login
# Enter username and password/token

# Tag image for DockerHub
docker tag flask-todo-api:v1 YOUR_USERNAME/flask-todo-api:v1

# Push to DockerHub
docker push YOUR_USERNAME/flask-todo-api:v1

# Anyone can now pull your image:
docker pull YOUR_USERNAME/flask-todo-api:v1
```

---

## Phase 3: CI with GitHub Actions

### 3.1 Create Workflow Directory
```bash
mkdir -p .github/workflows
```

### 3.2 GitHub Actions Workflow (.github/workflows/ci.yml)

```yaml
name: CI Pipeline

# When to trigger
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest  # GitHub-provided runner
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest -v --cov=app tests/

  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: test  # Only run if test job succeeds
    if: github.event_name == 'push'  # Only on pushes, not PRs
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/flask-todo-api:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/flask-todo-api:${{ github.sha }}
```

**Key Concepts:**
- `on:` - Event triggers
- `jobs:` - Units of work
- `runs-on:` - Where to run (GitHub's machines)
- `steps:` - Individual tasks
- `uses:` - Pre-built actions from marketplace
- `run:` - Shell commands
- `needs:` - Job dependencies
- `secrets:` - Encrypted credentials

### 3.3 Add Secrets to GitHub

1. Go to GitHub repo → **Settings**
2. **Secrets and variables** → **Actions**
3. **New repository secret**
4. Add:
   - `DOCKERHUB_USERNAME` - Your DockerHub username
   - `DOCKERHUB_TOKEN` - Access token (not password!)

### 3.4 Create DockerHub Access Token

1. hub.docker.com → Account Settings → Security
2. **New Access Token**
3. Name: `github-actions`
4. Permissions: Read, Write, Delete
5. Copy token immediately

### 3.5 Push and Watch

```bash
git add .
git commit -m "Add GitHub Actions CI"
git push origin main

# Go to GitHub repo → Actions tab
# Watch pipeline run automatically
```

---

## Phase 4: CI with Jenkins

### 4.1 Install Jenkins on EC2

```bash
# Install Java (required for Jenkins)
sudo apt update
sudo apt install openjdk-17-jdk -y
java -version

# Add Jenkins repository
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | \
  sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# Install Jenkins
sudo apt update
sudo apt install jenkins -y

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
sudo systemctl status jenkins

# Get initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 4.2 Configure EC2 Security Group

**AWS Console:**
1. EC2 → Security Groups
2. Add inbound rule:
   - Type: Custom TCP
   - Port: 8080
   - Source: 0.0.0.0/0 (or your IP)

### 4.3 Access Jenkins

1. Browser: `http://YOUR_EC2_IP:8080`
2. Paste initial admin password
3. Install suggested plugins
4. Create admin user
5. Save and continue

### 4.4 Install Required Plugins

**Manage Jenkins → Plugins → Available plugins**

Install:
- ✅ **Docker Pipeline** (REQUIRED for Docker agents)
- ✅ **Docker** (usually auto-installed)
- ✅ **Git**
- ✅ **GitHub Integration**

### 4.5 Give Jenkins Docker Access

```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins

# Restart Jenkins to pick up group change
sudo systemctl restart jenkins

# Verify jenkins can use Docker
sudo -u jenkins docker ps
```

### 4.6 Add DockerHub Credentials to Jenkins

1. **Manage Jenkins → Credentials**
2. Click **(global)** domain
3. **Add Credentials**
4. Fill in:
   - **Kind:** Username with password
   - **Scope:** Global
   - **Username:** Your DockerHub username
   - **Password:** DockerHub access token
   - **ID:** `dockerhub-credentials` (MUST be exactly this!)
   - **Description:** DockerHub Token
5. Click **Create**

### 4.7 Create Jenkinsfile

**Jenkinsfile** (in project root):

```groovy
pipeline {
    // Use Docker agent - runs inside Python container
    agent {
        docker {
            image 'python:3.11-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    
    environment {
        // Load credentials securely
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = "YOUR_USERNAME/flask-todo-api"
        IMAGE_TAG = "${BUILD_NUMBER}"  // Jenkins auto-increments
    }
    
    stages {
        stage('Setup') {
            steps {
                echo 'Installing Docker CLI inside container...'
                sh '''
                    apt-get update -qq
                    apt-get install -y docker.io
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh '''
                    pip install --no-cache-dir -r requirements.txt
                    pytest -v --cov=app tests/
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building Docker image...'
                sh """
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
                """
            }
        }
        
        stage('Push') {
            steps {
                echo 'Pushing to DockerHub...'
                sh """
                    echo \${DOCKERHUB_CREDENTIALS_PSW} | docker login -u \${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                    docker logout
                """
            }
        }
        
        stage('Cleanup') {
            steps {
                echo 'Cleaning up...'
                sh """
                    docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true
                    docker rmi ${IMAGE_NAME}:latest || true
                """
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline succeeded! ✅'
        }
        failure {
            echo 'Pipeline failed! ❌'
        }
        always {
            echo 'Cleaning workspace...'
            cleanWs()
        }
    }
}
```

**Key Jenkinsfile Concepts:**
- `pipeline` - Declarative pipeline syntax
- `agent` - Where to run (Docker container)
- `environment` - Variables available to all stages
- `credentials()` - Securely loads credentials
- `stages` - Pipeline phases
- `steps` - Actions within a stage
- `sh` - Run shell commands
- `post` - Actions after pipeline completes

### 4.8 Create Jenkins Pipeline

1. Jenkins Dashboard → **New Item**
2. Name: `flask-todo-api-pipeline`
3. Type: **Pipeline**
4. Click **OK**
5. Scroll to **Pipeline** section:
   - **Definition:** Pipeline script from SCM
   - **SCM:** Git
   - **Repository URL:** Your GitHub repo URL
   - **Branch:** `*/main`
   - **Script Path:** `Jenkinsfile`
6. **Save**

### 4.9 Run Pipeline

1. Click **Build Now**
2. Watch stages execute in real-time
3. Check Console Output for details
4. Verify image on DockerHub

### 4.10 Optional: GitHub Webhook (Auto-trigger)

**In Jenkins Pipeline:**
1. Configure → Build Triggers
2. Check **GitHub hook trigger for GITScm polling**
3. Save

**In GitHub Repo:**
1. Settings → Webhooks → Add webhook
2. Payload URL: `http://YOUR_EC2_IP:8080/github-webhook/`
3. Content type: `application/json`
4. Events: **Just the push event**
5. Add webhook

Now pushes to GitHub automatically trigger Jenkins builds!

---

## Key Concepts

### Continuous Integration (CI)
**Definition:** Automatically testing and building code on every commit

**Benefits:**
- Catches bugs early
- Ensures code always builds
- Maintains code quality
- Fast feedback to developers

### Docker Agent vs Host-Based Builds

**Host-Based (agent any):**
```groovy
pipeline {
    agent any  // Runs on Jenkins server directly
}
```
- ❌ Needs all tools installed (Python, Node, Java, etc.)
- ❌ Dependency conflicts possible
- ❌ Not scalable
- ✅ Faster (no container startup)

**Docker Agent:**
```groovy
pipeline {
    agent {
        docker { image 'python:3.11' }
    }
}
```
- ✅ Clean isolated environment
- ✅ Jenkins only needs Docker
- ✅ Different projects use different containers
- ✅ Production standard
- ⚠️ Slightly slower (pull image first time)

### Jenkins Credentials

**How it works:**
```groovy
environment {
    DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
}
```

Jenkins automatically creates:
- `DOCKERHUB_CREDENTIALS_USR` - username
- `DOCKERHUB_CREDENTIALS_PSW` - password (masked in logs)
- `DOCKERHUB_CREDENTIALS` - username:password combined

### Docker Layer Caching

**Why this order matters:**
```dockerfile
COPY requirements.txt .     # Changes rarely
RUN pip install...          # Cached if requirements unchanged
COPY . .                    # Changes frequently
```

**Efficient:** If only code changes, Docker reuses pip install layer
**Inefficient:** If we copied all files first, pip would reinstall every time

---

## Common Interview Questions

### Application Questions

**Q: Why did you choose Flask?**
A: Flask is lightweight, simple to understand, and perfect for learning CI/CD fundamentals. It has minimal boilerplate, making it easy to see what's happening at each step.

**Q: What does CORS do?**
A: CORS (Cross-Origin Resource Sharing) allows frontend applications from different domains to call my API. Without it, browsers block these requests for security.

**Q: Why use SQLite instead of MySQL/PostgreSQL?**
A: SQLite is file-based with no external dependencies, perfect for a learning project. It demonstrates database operations without needing a separate database server.

**Q: How do you test your API?**
A: I use pytest for unit tests, testing each endpoint individually. I also use curl for manual testing and can use tools like Postman for more complex scenarios.

### Docker Questions

**Q: What's the difference between a Docker image and container?**
A: 
- **Image:** Blueprint/template (like a class in OOP). Static, immutable.
- **Container:** Running instance of an image (like an object). Has state, can be started/stopped.

**Q: Why use Docker?**
A: 
- Consistency: "Works on my machine" → "Works everywhere"
- Isolation: No dependency conflicts
- Portability: Easy to ship and deploy
- Scalability: Spin up multiple containers easily

**Q: Explain your Dockerfile**
A:
1. Start with Python base image
2. Set working directory
3. Copy and install dependencies (cached layer)
4. Copy application code
5. Expose port for documentation
6. Define startup command

**Q: What is .dockerignore?**
A: Like .gitignore but for Docker. Excludes files from being copied into the image (venv, cache files, etc.). Makes images smaller and builds faster.

### CI/CD Questions

**Q: What is Continuous Integration?**
A: Automatically building and testing code every time developers commit. Catches bugs early and ensures code always works.

**Q: GitHub Actions vs Jenkins - when to use which?**
A:
- **GitHub Actions:** Quick setup, cloud-hosted, great for open source, free for public repos
- **Jenkins:** Self-hosted, more control, better for enterprises, no vendor lock-in

**Q: What's in your CI pipeline?**
A: 
1. Checkout code
2. Run unit tests (pytest)
3. Build Docker image
4. Push to DockerHub
5. Cleanup

**Q: How do you handle secrets?**
A: 
- **GitHub Actions:** Repository secrets (encrypted)
- **Jenkins:** Credentials plugin (encrypted, never in code)
- **Never:** Hardcode in code or commit to Git

**Q: What are the stages in your Jenkins pipeline?**
A:
1. **Setup:** Install Docker CLI in container
2. **Test:** Install deps and run pytest
3. **Build:** Create Docker image
4. **Push:** Upload to DockerHub
5. **Cleanup:** Remove local images

**Q: Why use Docker agent in Jenkins?**
A: 
- Clean Python 3.11 environment every build
- No need to install Python on Jenkins server
- Different projects can use different Docker images
- This is production standard

### Troubleshooting Questions

**Q: What was your biggest challenge?**
A: Getting Jenkins to access Docker. Learned that:
- Jenkins runs as `jenkins` user
- Must add to `docker` group
- Must restart Jenkins to pick up group membership
- Jenkins plugins ≠ system software

**Q: How did you debug issues?**
A:
- Read error messages carefully
- Check logs (`docker logs`, Jenkins console output)
- Test manually first (`docker ps`, `docker login`)
- Understand the system (users, groups, permissions)

### Architecture Questions

**Q: Draw your CI/CD architecture**
```
Developer → Git Push → GitHub
                         ↓
                    [Trigger]
                         ↓
           ┌─────────────┴──────────────┐
           ↓                            ↓
    GitHub Actions                   Jenkins (EC2)
           ↓                            ↓
    [Test → Build → Push]      [Test → Build → Push]
           ↓                            ↓
                    DockerHub
                         ↓
              [Production Deployment]
```

**Q: What happens when you push code?**
A:
1. Git push to GitHub
2. GitHub Actions triggers automatically
3. Jenkins webhook triggers (if configured)
4. Both run tests in parallel
5. If tests pass, build Docker image
6. Tag with build number and 'latest'
7. Push to DockerHub
8. Image available for deployment

---

## Troubleshooting Guide

### Issue: pip3 not found in Jenkins

**Symptom:**
```
pip3: not found
```

**Cause:** Jenkins doesn't have Python/pip installed or in PATH

**Solutions:**
1. **Use Docker agent** (recommended):
   ```groovy
   agent { docker { image 'python:3.11-slim' } }
   ```
2. **Install Python system-wide:**
   ```bash
   sudo apt install python3-pip -y
   ```
3. **Use full path:**
   ```bash
   /usr/bin/python3 -m pip install -r requirements.txt
   ```

### Issue: docker: not found in Jenkins

**Symptom:**
```
docker: not found
```

**Cause:** Docker not installed or Jenkins can't access it

**Solutions:**
```bash
# Install Docker
sudo apt install docker.io -y

# Add jenkins to docker group
sudo usermod -aG docker jenkins

# Restart Jenkins (CRITICAL!)
sudo systemctl restart jenkins

# Verify
sudo -u jenkins docker ps
```

### Issue: Invalid agent type "docker"

**Symptom:**
```
Invalid agent type "docker" specified. Must be one of [any, label, none]
```

**Cause:** Docker Pipeline plugin not installed

**Solution:**
1. Manage Jenkins → Plugins
2. Search "Docker Pipeline"
3. Install and restart Jenkins

### Issue: Docker login unauthorized

**Symptom:**
```
Error response from daemon: unauthorized: incorrect username or password
```

**Solutions:**
1. **Use access token, not password:**
   - hub.docker.com → Security → New Access Token
2. **Check username capitalization:**
   - Must match exactly (case-sensitive)
3. **Recreate Jenkins credential:**
   - Delete old one
   - Create new with correct username and token
4. **Test manually first:**
   ```bash
   echo "YOUR_TOKEN" | docker login -u YOUR_USERNAME --password-stdin
   ```

### Issue: Permission denied on docker.sock

**Symptom:**
```
permission denied while trying to connect to Docker daemon
```

**Cause:** User not in docker group

**Solution:**
```bash
sudo usermod -aG docker jenkins
sudo usermod -aG docker ubuntu
sudo systemctl restart jenkins
# Or reboot: sudo reboot
```

### Issue: Tests fail in Jenkins but pass locally

**Possible causes:**
1. **Different Python versions:**
   - Solution: Use same version in Dockerfile/agent
2. **Missing dependencies:**
   - Solution: Check requirements.txt is complete
3. **Environment variables:**
   - Solution: Set in Jenkins pipeline
4. **File permissions:**
   - Solution: Check file ownership

### Issue: Docker image build fails

**Common causes:**
1. **Syntax error in Dockerfile:**
   - Test locally: `docker build -t test .`
2. **Network issues pulling base image:**
   - Check: `docker pull python:3.11-slim`
3. **Dependencies fail to install:**
   - Check requirements.txt syntax
4. **Out of disk space:**
   - Check: `df -h`
   - Clean: `docker system prune -a`

---

## Quick Command Reference

### Docker Commands
```bash
# Build image
docker build -t myapp:v1 .

# Run container
docker run -d -p 5000:5000 --name myapp myapp:v1

# List running containers
docker ps

# List all containers
docker ps -a

# View logs
docker logs myapp

# Stop container
docker stop myapp

# Remove container
docker rm myapp

# List images
docker images

# Remove image
docker rmi myapp:v1

# Login to DockerHub
docker login

# Tag image
docker tag myapp:v1 username/myapp:v1

# Push to DockerHub
docker push username/myapp:v1

# Clean up
docker system prune -a  # Remove all unused images/containers
```

### Git Commands
```bash
# Initialize repo
git init

# Add files
git add .

# Commit
git commit -m "message"

# Add remote
git remote add origin https://github.com/user/repo.git

# Push
git push origin main

# Check status
git status

# View log
git log --oneline
```

### Jenkins CLI
```bash
# Restart Jenkins
sudo systemctl restart jenkins

# Check status
sudo systemctl status jenkins

# View logs
sudo journalctl -u jenkins -f

# Get initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### Testing
```bash
# Run all tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=app tests/

# Specific test
pytest tests/test_app.py::test_health_check
```

---

## Production Best Practices

### 1. Never Hardcode Secrets
❌ **Bad:**
```python
PASSWORD = "secret123"
```

✅ **Good:**
```python
PASSWORD = os.environ.get('PASSWORD')
```

### 2. Use .gitignore
Always exclude:
- `.env` files
- `venv/`
- `*.db`
- `__pycache__/`
- `.pytest_cache/`

### 3. Pin Dependency Versions
❌ **Bad:**
```
Flask
pytest
```

✅ **Good:**
```
Flask==3.0.0
pytest==7.4.3
```

### 4. Use Docker Layer Caching
Copy dependencies first, code last:
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### 5. Run Tests Before Deploy
Never skip tests in CI pipeline:
```groovy
needs: test  // In GitHub Actions
```

### 6. Tag Images with Versions
❌ **Bad:** Only `:latest`
✅ **Good:** `:latest` AND `:v1.2.3` or `:build-123`

### 7. Use Minimal Base Images
```dockerfile
FROM python:3.11-slim  # Not python:3.11-full
```

### 8. Clean Up Resources
```groovy
stage('Cleanup') {
    steps {
        sh 'docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true'
    }
}
```

---

## Next Steps for Learning

### After Mastering CI:

1. **Continuous Deployment (CD)**
   - Deploy to EC2 automatically
   - Deploy to Kubernetes
   - Blue-green deployments
   - Canary releases

2. **Infrastructure as Code**
   - Terraform for AWS resources
   - Ansible for configuration
   - CloudFormation

3. **Container Orchestration**
   - Kubernetes basics
   - Helm charts
   - Service mesh (Istio)

4. **Monitoring & Logging**
   - Prometheus + Grafana
   - ELK Stack
   - CloudWatch

5. **Other Tech Stacks**
   - Node.js + Express
   - Java + Spring Boot
   - Go REST API
   - MERN full-stack

---

## Interview Tips

### Technical Interview:

1. **Explain your choices:** "I used Docker because..."
2. **Show problem-solving:** "When I got X error, I troubleshot by..."
3. **Understand concepts, not just commands:** Know WHY, not just HOW
4. **Draw diagrams:** Visualize architecture
5. **Admit what you don't know:** "I haven't used X yet, but I've used similar Y..."

### Behavioral Interview:

1. **Challenges overcome:** "Jenkins couldn't find Docker, learned about Linux users/groups..."
2. **Learning process:** "Built from scratch to understand fundamentals..."
3. **Curiosity:** "Compared GitHub Actions vs Jenkins to see trade-offs..."
4. **Documentation:** "Created detailed notes for team knowledge sharing..."

### Portfolio:

Point to your GitHub repo:
- ✅ Clean code with comments
- ✅ README with setup instructions
- ✅ Working CI/CD pipelines
- ✅ Tests with good coverage
- ✅ Proper .gitignore, .dockerignore

---

## Summary

### What You Built:
A production-grade CI pipeline that automatically tests, builds, and publishes a containerized Python application using both GitHub Actions and Jenkins.

### Skills Demonstrated:
- Application development (Python, Flask, REST APIs)
- Testing (pytest, unit tests, coverage)
- Containerization (Docker, Dockerfile, images)
- CI/CD (GitHub Actions, Jenkins)
- Cloud (AWS EC2)
- DevOps practices (IaC, automation, pipelines)
- Troubleshooting (debugging, logs, permissions)

### Time Investment:
- Phase 1 (App): 2-3 hours
- Phase 2 (Docker): 1-2 hours
- Phase 3 (GitHub Actions): 1 hour
- Phase 4 (Jenkins): 2-3 hours
- **Total:** 6-9 hours for complete mastery

### Interview Readiness:
You can now confidently discuss:
- How CI/CD works
- Docker containerization
- Pipeline automation
- Cloud deployment
- DevOps best practices

---
