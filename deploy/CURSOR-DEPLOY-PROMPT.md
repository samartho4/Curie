Deploy the Slack agent in `~/Pictures/Slack4Good` to an always-on AWS EC2 instance. It must run 24/7 for judging (Jul 14–Aug 6). It's a **Socket Mode** Bolt (Python) app — it dials OUT to Slack, so it needs **no inbound web ports at all**.

Server-side setup is already automated in this repo. Do NOT redesign it — execute the runbook `deploy/aws-ec2.md` using the provisioner `deploy/setup-ec2.sh`. Use my AWS credits.

## Do exactly this
1. **Preflight (secrets):** confirm `~/Pictures/Slack4Good/.env` exists and `git check-ignore .env` prints `.env`. Never print, commit, upload, or bake tokens into an AMI/user-data/S3/logs. The only place `.env` may go is the rsync to our own EC2 box (below).
2. **Launch one instance** in my default region:
   - AMI: latest Amazon Linux 2023 via SSM param `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`
   - Type: `t3.small`
   - Key pair: create `curie-key`, save private key to `~/curie-key.pem`, `chmod 400`
   - Security group `curie-sg`: inbound **tcp/22 from my public IP /32 ONLY** (`curl -s https://checkip.amazonaws.com`); outbound = default allow-all. **No other inbound rule. Never 0.0.0.0/0 on any port.**
   - Tag `Name=curie`. Wait for `running` + 2/2 status checks. Capture InstanceId + Public DNS.
3. **Copy code** Mac→box (includes `.env`; SSH is encrypted, it's our box):
   ```
   rsync -avz -e "ssh -i ~/curie-key.pem -o StrictHostKeyChecking=accept-new" \
     --exclude '.git' --exclude '__pycache__' --exclude '.venv' --exclude '.DS_Store' \
     ~/Pictures/Slack4Good/  ec2-user@<PUBLIC_DNS>:~/Slack4Good/
   ```
4. **Provision + start:** `ssh -i ~/curie-key.pem ec2-user@<PUBLIC_DNS> 'bash ~/Slack4Good/deploy/setup-ec2.sh'`
   (installs Python 3.11 + venv + deps + a systemd service `curie` that auto-restarts on crash/reboot).
5. **Share the Lab Record** once so judges can open it: `ssh -i ~/curie-key.pem ec2-user@<PUBLIC_DNS> 'cd ~/Slack4Good && ./.venv/bin/python -m scripts.share_list'`
6. **Stop the duplicate:** once step 7 passes, stop the copy of `app.py` still running on my Mac (Ctrl+C / kill it) so EC2 is the ONLY responder. (Two live copies on the same tokens = ambiguous handling.)

## Verify, then REPORT all of this back verbatim
- `sudo systemctl status curie --no-pager`  → must be **active (running)**
- `sudo journalctl -u curie -n 40 --no-pager`  → must contain **"Curie is listening (Socket Mode)"**, and must NOT show a restart loop or a "missing env vars" error
- `aws ec2 describe-security-groups --group-names curie-sg --query 'SecurityGroups[0].IpPermissions'` → confirm only tcp/22 from my /32
- InstanceId, Public DNS, region, instance type

## Guardrails
- If a step needs a judgment call you can't make safely (especially security groups or secrets), **STOP and report** — do not improvise.
- Provision exactly one instance, one security group, one key pair. Nothing world-open. No secrets anywhere public.

## Done when
`systemctl status curie` = active (running) AND journalctl shows "Curie is listening" AND `curie-sg` exposes only SSH to my IP. Paste the four verification outputs above plus InstanceId / Public DNS so my principal agent can check it.
