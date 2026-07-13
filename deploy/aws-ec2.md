# Deploy Curie on AWS EC2 (direct, no GitHub)

Always-on box for the Socket Mode agent. **No inbound web ports needed** — the agent dials out to
Slack, so the only inbound rule is SSH (port 22) from your IP. Code goes Mac → EC2 over `rsync`.

Total time ~15 min. Costs are trivial (t3.small ≈ a few $/mo, covered by your credits); terminate after Aug 6.

---

## 1. Launch the instance

**Console:** EC2 → Launch instance →
- Name `curie` · AMI **Amazon Linux 2023** · type **t3.small** (t3.micro is fine too)
- Key pair → **Create new** → download `curie-key.pem`
- Network settings → Security group: allow **SSH (22) from My IP** only. Leave outbound as default (all).
- Launch. Copy the instance's **Public IPv4 DNS** (e.g. `ec2-1-2-3-4.compute-1.amazonaws.com`).

**Or CLI** (uses your default VPC; resolves the latest AL2023 AMI automatically):
```bash
aws ec2 create-key-pair --key-name curie-key --query KeyMaterial --output text > ~/curie-key.pem
chmod 400 ~/curie-key.pem
SG=$(aws ec2 create-security-group --group-name curie-sg --description "Curie SSH" --query GroupId --output text)
MYIP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 22 --cidr ${MYIP}/32
aws ec2 run-instances --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --instance-type t3.small --key-name curie-key --security-group-ids $SG \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=curie}]' \
  --query 'Instances[0].InstanceId' --output text
# then: aws ec2 describe-instances --filters Name=tag:Name,Values=curie --query 'Reservations[].Instances[].PublicDnsName' --output text
```

## 2. Copy the code (and .env) from your Mac

```bash
chmod 400 ~/curie-key.pem   # or wherever the .pem downloaded
HOST=ec2-user@<PUBLIC_DNS>

rsync -avz -e "ssh -i ~/curie-key.pem" \
  --exclude '.git' --exclude '__pycache__' --exclude '.venv' --exclude '.DS_Store' \
  ~/Pictures/Slack4Good/  $HOST:~/Slack4Good/
```
The `rsync` includes `.env` — that's fine, SSH is encrypted and it's your box. (If you'd rather keep
secrets out of rsync, add `--exclude '.env'` and `scp` it separately.)

## 3. Provision + start (one command on the box)

```bash
ssh -i ~/curie-key.pem $HOST
bash ~/Slack4Good/deploy/setup-ec2.sh
```
That installs Python 3.11, a venv, dependencies, and a **systemd service that auto-restarts on crash
or reboot**.

## 4. Verify

```bash
sudo journalctl -u curie -f          # expect: "Curie is listening (Socket Mode)."
```
Then in Slack #experiments: `@Prior <a plan>` — or DM Prior. You should see the streamed check + card.

## 5. Update after a code change

```bash
# from the Mac: rsync again (step 2), then on the box:
sudo systemctl restart curie
```

## 6. Teardown (after judging, ~Aug 6)

```bash
sudo systemctl disable --now curie          # on the box, or just:
aws ec2 terminate-instances --instance-ids <id>
```

---

### Notes
- **Only the Mac→EC2 copy and the instance launch touch your AWS keys/SSH — those are yours to run.**
  Everything server-side is automated by `setup-ec2.sh`.
- The service runs `app.py`, which loads `.env` via python-dotenv from `~/Slack4Good`. No secrets live
  in the systemd unit.
- Watch for a crash-loop in `journalctl` right after start — it almost always means `.env` is missing
  or a token is wrong.
