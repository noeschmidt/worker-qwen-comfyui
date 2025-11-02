# Configuration pour les modèles Qwen sur RunPod

Ce document explique les modifications apportées au projet pour utiliser les modèles Qwen depuis votre network volume RunPod.

## Modèles utilisés

Les modèles Qwen sont stockés sur votre network volume RunPod à l'emplacement suivant :

```
/runpod-volume/runpod-slim/ComfyUI/models/
├── diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors
├── loras/Qwen-Image-Lightning-4steps-V1.0.safetensors
├── vae/qwen_image_vae.safetensors
└── text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors
```

## Fichiers modifiés

### 1. `src/extra_model_paths.yaml`

Ce fichier configure les chemins des modèles pour ComfyUI. Les modifications incluent :

- **`base_path`** : Changé de `/runpod-volume` à `/runpod-volume/runpod-slim/ComfyUI`
- **Ajout de nouveaux chemins** :
  - `diffusion_models: models/diffusion_models/`
  - `text_encoders: models/text_encoders/`

Ces chemins permettent à ComfyUI de trouver automatiquement vos modèles Qwen sur le network volume.

### 2. `Dockerfile`

Installation du package custom node **`Comfyui-QwenEditUtils`** (ligne 91-93) pour supporter le node `TextEncodeQwenImageEditPlus`.

```dockerfile
# Install custom nodes for Qwen models (TextEncodeQwenImageEditPlus)
# Source: https://registry.comfy.org/fr/nodes/qweneditutils
RUN comfy-node-install Comfyui-QwenEditUtils
```

**Note** : Les nodes `ModelSamplingAuraFlow` et `CFGNorm` sont standard dans ComfyUI et n'ont pas besoin de custom nodes supplémentaires.

### 3. `workflows/renovate_workflow-api.json`

Aucune modification nécessaire ! Le workflow référence déjà correctement les noms de fichiers des modèles :

- `qwen_image_edit_2509_fp8_e4m3fn.safetensors` (UNETLoader)
- `Qwen-Image-Lightning-4steps-V1.0.safetensors` (LoraLoaderModelOnly)
- `qwen_image_vae.safetensors` (VAELoader)
- `qwen_2.5_vl_7b_fp8_scaled.safetensors` (CLIPLoader)

## Custom Nodes installés

Votre workflow utilise principalement des **nodes standard de ComfyUI** :

✅ **Nodes standards (inclus dans ComfyUI de base)** :

- `SaveImage`, `LoadImage`, `PreviewImage`
- `VAELoader`, `VAEDecode`, `VAEEncode`
- `CLIPLoader`
- `UNETLoader`
- `LoraLoaderModelOnly`
- `KSampler`
- `EmptySD3LatentImage`
- `ImageScaleToTotalPixels`
- `ModelSamplingAuraFlow`
- `CFGNorm`

✅ **Custom node installé** :

- **`Comfyui-QwenEditUtils`** : Fournit le node `TextEncodeQwenImageEditPlus` requis pour l'encodage de texte spécifique à Qwen Image Edit
- Source : https://registry.comfy.org/fr/nodes/qweneditutils

## Étapes de déploiement

### 1. Vérifier que les modèles sont bien sur le network volume

⚠️ **Important** : Le point de montage du network volume diffère entre Pod et Serverless :

| Type de déploiement | Point de montage | Chemin complet exemple                                        |
| ------------------- | ---------------- | ------------------------------------------------------------- |
| **Pod**             | `/workspace`     | `/workspace/runpod-slim/ComfyUI/models/diffusion_models/`     |
| **Serverless**      | `/runpod-volume` | `/runpod-volume/runpod-slim/ComfyUI/models/diffusion_models/` |

Notre configuration utilise `/runpod-volume` (pour serverless). Les deux pointent vers le même stockage S3.

**Vérification depuis un Pod** :

```bash
# Dans un pod, le network volume est monté à /workspace
ls -lh /workspace/runpod-slim/ComfyUI/models/diffusion_models/
ls -lh /workspace/runpod-slim/ComfyUI/models/loras/
ls -lh /workspace/runpod-slim/ComfyUI/models/vae/
ls -lh /workspace/runpod-slim/ComfyUI/models/text_encoders/
```

**Vérification depuis S3** :

```bash
aws s3 ls --region eu-ro-1 --endpoint-url https://s3api-eu-ro-1.runpod.io \
  s3://np04a8r06z/runpod-slim/ComfyUI/models/diffusion_models/
```

Si vos fichiers sont visibles depuis le Pod à `/workspace/runpod-slim/...`, ils seront automatiquement disponibles en serverless à `/runpod-volume/runpod-slim/...`

### 2. Builder l'image Docker

⚠️ **Important pour Mac (Apple Silicon)** : RunPod nécessite une image `linux/amd64`. Utilisez `--platform` :

```bash
# Pour Mac Apple Silicon (M1/M2/M3) ou toute architecture ARM
docker build --platform linux/amd64 -t noeschmidt/worker-comfyui-qwen:latest .

# Alternative si vous avez activé buildx
docker buildx build --platform linux/amd64 -t your-username/worker-comfyui-qwen:latest --push .
```

**Note** : Le build peut être plus lent sur Mac car il utilise l'émulation QEMU pour construire une image x86_64.

⏱️ **Temps de build attendu sur Mac Apple Silicon** :
- Premier build : **15-30 minutes** (peut aller jusqu'à 45 min)
- Étapes les plus longues :
  - Installation de ComfyUI (~5-15 min)
  - Installation de Comfyui-QwenEditUtils (~2-5 min)
- Les builds suivants seront plus rapides grâce au cache Docker

💡 **Astuce** : Si c'est trop long, vous pouvez builder directement sur un Pod RunPod (architecture amd64 native).

### 3. Pusher l'image sur Docker Hub

Si vous n'avez pas utilisé `--push` avec buildx :

```bash
docker push your-username/worker-comfyui-qwen:latest
```

### 4. Configurer l'endpoint RunPod

Dans la configuration de votre endpoint serverless RunPod :

- **Container Image** : `your-username/worker-comfyui-qwen:latest`
- **Network Volume** : Attachez votre network volume (ID: `np04a8r06z`)
- **Environment Variables** (optionnel) :
  - `COMFY_LOG_LEVEL=DEBUG` (pour plus de logs)
  - `REFRESH_WORKER=true` (pour redémarrer le worker après chaque job)

## Test du workflow

Une fois le endpoint déployé, testez avec le payload généré :

```bash
cd workflows
python3 generate_postman_payload.py
```

Puis envoyez la requête à votre endpoint :

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @postman_payload.json
```

## Troubleshooting

### Erreur : "exec format error" ou l'image ne démarre pas

Si votre container ne démarre pas avec une erreur de format :

1. Vous avez probablement oublié `--platform linux/amd64` lors du build
2. Rebuilder l'image avec la bonne plateforme :
   ```bash
   docker build --platform linux/amd64 -t your-username/worker-comfyui-qwen:latest .
   ```
3. Vérifier l'architecture de votre image :
   ```bash
   docker inspect your-username/worker-comfyui-qwen:latest | grep Architecture
   # Doit afficher "Architecture": "amd64"
   ```

### Erreur : "Model not found"

Si vous obtenez une erreur indiquant que le modèle n'est pas trouvé :

1. Vérifiez que le network volume est bien **attaché** à votre endpoint serverless
2. Vérifiez que les chemins dans `extra_model_paths.yaml` utilisent `/runpod-volume` (pour serverless)
3. Vérifiez que vos modèles sont bien à `/workspace/runpod-slim/...` dans un pod (ce qui correspond à `/runpod-volume/runpod-slim/...` en serverless)
4. Vérifiez les permissions des fichiers sur le network volume

### Erreur : "Node type not found"

Si vous obtenez une erreur sur un type de node :

1. Vérifiez que les custom nodes Qwen sont bien installés
2. Consultez les logs du build Docker
3. Vérifiez le nom du package sur https://registry.comfy.org/

### Les modèles ne se chargent pas

Si ComfyUI ne trouve pas les modèles malgré la configuration :

1. Connectez-vous à un pod avec le network volume
2. Vérifiez l'arborescence exacte :
   ```bash
   tree -L 4 /runpod-volume/runpod-slim/ComfyUI/models/
   ```
3. Ajustez `extra_model_paths.yaml` si nécessaire

## Références

- [RunPod Network Storage Documentation](https://docs.runpod.io/pods/storage/network-storage)
- [ComfyUI Custom Nodes Registry](https://registry.comfy.org/)
- [Worker ComfyUI Repository](https://github.com/blib-la/runpod-worker-comfy)
