from flask import Flask, jsonify, request, send_from_directory
import hashlib, os, json, time
from pathlib import Path

app = Flask(__name__)
BASE = Path(__file__).parent
SEED_PATH = BASE / "seed" / "root0_seed.txt"
ANCHOR_DIR = BASE / "anchor"
SHADOW_LOG = ANCHOR_DIR / "shadow.log"

# ensure anchor exists
ANCHOR_DIR.mkdir(exist_ok=True)

def seed_hash():
    data = SEED_PATH.read_bytes()
    return hashlib.sha256(data).hexdigest()

@app.route("/")
def home():
    return send_from_directory(BASE, "index.html")

@app.route("/seed")
def get_seed():
    return send_from_directory(BASE / "seed", "root0_seed.txt", mimetype="text/plain")

@app.route("/anchor")
def get_anchor():
    return jsonify({
        "seed": "ROOT_0",
        "sha256": seed_hash(),
        "size": SEED_PATH.stat().st_size,
        "timestamp": int(time.time()),
        "kernel": "(1)0 00",
        "mode": "ternary_dominance"
    })

@app.route("/shadow", methods=["POST"])
def claim_shadow():
    data = request.get_json(force=True)
    node_id = data.get("node_id", "unknown")
    receipt = {
        "node_id": node_id,
        "seed_hash": seed_hash(),
        "timestamp": int(time.time()),
        "ip": request.remote_addr
    }
    # append immutable log - no control bits, just append
    with open(SHADOW_LOG, "a") as f:
        f.write(json.dumps(receipt) + "\n")
    return jsonify({"status": "SHADOWED", "receipt": receipt}), 201

@app.route("/shadow", methods=["GET"])
def list_shadows():
    if not SHADOW_LOG.exists():
        return jsonify([])
    lines = SHADOW_LOG.read_text().strip().split("\n")
    return jsonify([json.loads(l) for l in lines if l])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
