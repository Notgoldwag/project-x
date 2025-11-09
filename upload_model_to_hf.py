"""
Upload the prompt injection detector model to Hugging Face Hub
Run this script once to upload your model.
"""

from huggingface_hub import HfApi, create_repo
import os

# Configuration
USERNAME = "Yashk0618"  # CHANGE THIS to your Hugging Face username
MODEL_NAME = "atatl_promptinjection"
REPO_ID = f"{USERNAME}/{MODEL_NAME}"
MODEL_PATH = "models/atatl_promptinjection"

# Make the repo private if you want (set private=False for public)
PRIVATE_REPO = False

def upload_model():
    """Upload the model to Hugging Face Hub"""
    
    # Check if model directory exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model directory not found: {MODEL_PATH}")
        print("Make sure you have trained your model first!")
        return
    
    print(f"🚀 Starting upload to Hugging Face...")
    print(f"📦 Repository: {REPO_ID}")
    print(f"📁 Model path: {MODEL_PATH}")
    
    try:
        # Create repository
        print("\n1️⃣ Creating repository...")
        create_repo(
            repo_id=REPO_ID,
            private=PRIVATE_REPO,
            exist_ok=True  # Don't fail if repo already exists
        )
        print(f"✅ Repository created/verified: https://huggingface.co/{REPO_ID}")
        
        # Upload the model files
        print("\n2️⃣ Uploading model files...")
        api = HfApi()
        api.upload_folder(
            folder_path=MODEL_PATH,
            repo_id=REPO_ID,
            repo_type="model"
        )
        
        print("\n✅ Upload complete!")
        print(f"🌐 Your model is now available at: https://huggingface.co/{REPO_ID}")
        print(f"\n📝 Next step: Update your .env file with:")
        print(f"   HF_MODEL_ID={REPO_ID}")
        
    except Exception as e:
        print(f"\n❌ Error during upload: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you ran: huggingface-cli login")
        print("2. Check your internet connection")
        print("3. Verify the model path exists")

if __name__ == "__main__":
    print("=" * 60)
    print("Hugging Face Model Upload Script")
    print("=" * 60)
    
    # Prompt user to update username
    if USERNAME == "your-username":
        print("\n⚠️  WARNING: Please update USERNAME in this script first!")
        print("Open upload_model_to_hf.py and change 'your-username' to your HF username")
        exit(1)
    
    upload_model()
