#!/usr/bin/env python3
"""
Deployment script for the Modal embedder service.
"""

import modal
import subprocess
import sys
import time

def deploy_app():
    """Deploy the embedder app to Modal."""
    try:
        print("🚀 Deploying Nobel embedder to Modal...")
        
        # Deploy using modal CLI
        result = subprocess.run(
            ["modal", "deploy", "modal_embedder.py"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        if result.returncode == 0:
            print("✅ Deployment successful!")
            print(result.stdout)
            return True
        else:
            print("❌ Deployment failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Modal CLI not found. Please install Modal first:")
        print("   pip install modal")
        return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def check_app_status():
    """Check if the app is deployed and running."""
    try:
        print("🔍 Checking app status...")
        stub = modal.App.lookup("nobel-embedder")
        
        # Try to call health check
        health_check = stub.function("health_check")
        result = health_check.remote()
        
        print(f"✅ App is running: {result}")
        return True
        
    except modal.error.NotFoundError:
        print("❌ App not found - needs to be deployed")
        return False
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def main():
    """Main deployment function."""
    print("🎯 Nobel Embedder Service Deployment")
    print("=" * 40)
    
    # Check if app exists
    if check_app_status():
        print("\n✅ App is already deployed and running!")
        return
    
    # Deploy the app
    if deploy_app():
        print("\n⏳ Waiting for deployment to stabilize...")
        time.sleep(10)
        
        # Verify deployment
        if check_app_status():
            print("\n🎉 Deployment verified successfully!")
        else:
            print("\n⚠️  Deployment may have issues. Check logs with:")
            print("   modal logs nobel-embedder")
    else:
        print("\n❌ Deployment failed. Check the error messages above.")

if __name__ == "__main__":
    main() 