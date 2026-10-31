#!/bin/bash
cd /var/lib/alan-portfolio/workspaces/ryan/nexus-lab-ryan-vo/backend
python -m py_compile app/core/oidc.py app/api/auth.py app/core/security.py app/api/sessions.py app/api/observations.py app/main.py
echo "Syntax check passed"
