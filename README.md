# Hello Docker — CI/CD POC (Jenkins → Docker Hub → Kubernetes)

A compact DevOps proof-of-concept demonstrating a Jenkins pipeline that builds a Docker image from a simple Flask "Hello" application, pushes it to Docker Hub, and deploys to a local Kubernetes cluster (Minikube). The pipeline is triggered from GitHub (webhook) and runs on a local Jenkins instance at `http://localhost:8080`.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Architecture (text diagram)](#architecture-text-diagram)
- [Prerequisites](#prerequisites)
- [Repository layout](#repository-layout)
- [Local setup](#local-setup)
- [Jenkins setup](#jenkins-setup)
- [Kubernetes deployment](#kubernetes-deployment)
- [Triggering the pipeline](#triggering-the-pipeline)
- [Expected pipeline stages](#expected-pipeline-stages)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

---

## Project overview
This repository demonstrates a simple CI/CD flow optimized for local POC and review:

- Source: GitHub (trigger via webhook)
- CI/CD: Jenkins Pipeline (defined in `Jenkinsfile`)
- Build: Docker image built from `Dockerfile`
- Registry: Docker Hub (image tagging and pushes from Jenkins)
- Deploy: Kubernetes (Minikube) via `kubectl` applied from Jenkins using a kubeconfig secret

The application is a minimal Flask app (`app.py`) listening on port `5000`.

---

## Prerequisites

- Git
- Docker (required if Jenkins uses the local Docker daemon to build images)
- Minikube (local Kubernetes cluster)
- kubectl (configured locally for Minikube)
- Jenkins (accessible at `http://localhost:8080`)
- Docker Hub account
- GitHub repository and admin access (to create webhooks)

Notes:
- Jenkins agents executing the pipeline must have access to `docker` and `kubectl` (install or provide them in the agent container).
- The pipeline expects these credential IDs in Jenkins (see Jenkins setup): `docker_hub_pw`, `kubeconfig-minikube`.

---

## Repository layout

- `app.py` — Flask application (port `5000`)
- `Dockerfile` — builds the container image
- `Jenkinsfile` — declarative pipeline for CI/CD
- `k8s/deployment.yaml` — Deployment manifest (uses placeholder `DOCKER_IMAGE`)
- `k8s/service.yaml` — Service manifest (NodePort mapping to container port 5000)
- `requirements.txt` — Python dependencies

Important resources in manifests:
- Deployment name: `hello-app`
- Service name: `hello-service`
- Container port: `5000`

---

## Local setup (run & test locally)

1. Clone repository

```bash
git clone <repo-url>
cd hello-docker-k8s-ci-cd
```

2. Run locally without Docker

```bash
python -m pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

3. Build & run with Docker

```bash
docker build -t <your-dockerhub-user>/hello-app:local .
docker run --rm -p 5000:5000 <your-dockerhub-user>/hello-app:local
# Open http://localhost:5000
```

4. Deploy to Minikube for local verification

```bash
minikube start
kubectl apply -f k8s/
minikube service hello-service --url
# Or: kubectl port-forward svc/hello-service 8080:80
# Open the URL returned or http://localhost:8080
```

Note: `k8s/deployment.yaml` contains `image: DOCKER_IMAGE` which the pipeline replaces with the built image tag prior to `kubectl apply`.

---

## Jenkins setup (credentials, webhook, pipeline)

1. Jenkins and plugin requirements
   - Install Jenkins and plugins: Git, GitHub, Pipeline, Credentials, and any Docker/Kubernetes-related tools you need.

2. Credentials (create in Jenkins Credentials store)
   - Docker Hub token/password: **Secret text** or **Username/Password** credential
     - Example Jenkins credential ID used in `Jenkinsfile`: `docker_hub_pw` (string or secret)
   - Kubeconfig (Minikube) for Kubernetes access: **Secret File**
     - Example credential ID used in `Jenkinsfile`: `kubeconfig-minikube`

3. GitHub webhook
   - Add webhook in GitHub repo settings pointing to:
     `http://<jenkins-host>:8080/github-webhook/`
   - Trigger on `push` events (and optionally PR events)

4. Pipeline job
   - Create a Pipeline job that uses the repository and the included `Jenkinsfile`.
   - Ensure the job accepts GitHub webhooks (verify the GitHub plugin and webhook settings).

5. Verify environment variables in `Jenkinsfile`
   - `DOCKER_USER`, `DOCKER_IMAGE` (e.g., `mrlaw/hello-app`), and `IMAGE_TAG` are set in the file. Update them to match your Docker Hub username or configure them as job-level or global env vars.

Security note: Use Jenkins credentials and avoid hardcoding secrets.

---

## Kubernetes deployment explanation

- Manifests: `k8s/deployment.yaml` and `k8s/service.yaml`.
  - `deployment.yaml` has a placeholder `DOCKER_IMAGE` that the pipeline replaces with the built image (`${DOCKER_IMAGE}:${IMAGE_TAG}`).
  - `service.yaml` exposes the app via a `NodePort` on port `80` → `targetPort: 5000`.
- Deployment strategy in the pipeline: modify manifest to reference the new image and run `kubectl apply -f k8s/deployment.yaml`.
- Access:
  - `minikube service hello-service --url` or `kubectl port-forward` for local testing.

For production-grade workflows, consider templating (Helm/Kustomize), health probes, and proper rollout/rollback strategies.

---

## How to trigger the pipeline

- Push to the GitHub repository (webhook triggers Jenkins).
- Manually trigger from Jenkins UI (Build Now).
- Configure PR-related triggers if you want builds on pull requests.

---

## Expected pipeline stages (from `Jenkinsfile`)

1. Checkout — pull the repository
2. Build Docker Image — `docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .`
3. Docker Login — log in using `docker_hub_pw` credential
4. Push Docker Image — push tagged image and tag `latest`
5. Deploy to Kubernetes — replace `DOCKER_IMAGE` placeholder and `kubectl apply -f k8s/deployment.yaml`

These stages can be extended to include unit tests, container scans, linting, and integration tests.

---

## Troubleshooting (common issues & checks)

- Webhook not triggering:
  - Check GitHub webhook delivery logs and Jenkins' webhook endpoint reachability.
  - If Jenkins is local, use a tunnel (ngrok/localtunnel) for GitHub to reach it.

- Docker push/auth failures:
  - Confirm `docker_hub_pw` is correctly configured and matches the Docker Hub account.
  - Use a Docker Hub token if your account has 2FA enabled.

- Jenkins cannot execute Docker commands:
  - Ensure Docker is installed on the agent or use Docker-in-Docker with proper socket mounts.

- `kubectl` errors / kubeconfig problems:
  - Ensure `kubeconfig-minikube` contains a valid kubeconfig and Minikube is running.
  - Validate `KUBECONFIG` is being set from the secret file in the pipeline steps.

- Image not updating in the cluster:
  - Check `imagePullPolicy` (for testing use `Always` or unique tags).
  - Inspect rollout status: `kubectl rollout status deployment/hello-app`.

Helpful commands:

```bash
kubectl get pods,svc,deploy
kubectl logs <pod-name>
kubectl describe pod <pod-name>
kubectl rollout status deployment/hello-app
minikube service hello-service --url
```

---

## Cleanup

Remove Kubernetes resources:

```bash
kubectl delete -f k8s/
minikube stop
```

Remove local Docker images (optional):

```bash
docker image rm <your-image>
```

---
