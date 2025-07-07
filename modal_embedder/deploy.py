#!/usr/bin/env python3
"""
Deployment script for the Modal embedder service.

This script automates the deployment of the NobelLM embedder service to Modal.
It handles deployment, verification, and status checking of the embedder app.

Features:
- Automated deployment using Modal CLI
- Health check verification
- Error handling and logging
- Deployment status monitoring

Usage:
    python deploy.py

Author: NobelLM Team
Date: 2025
"""

import modal
import subprocess
import sys
import time

def deploy_app():
    """
    Deploy the embedder app to Modal using the CLI.
    
    This function uses the Modal CLI to deploy the modal_embedder.py file.
    It captures and displays the deployment output for monitoring.
    
    Returns:
        bool: True if deployment succeeds, False otherwise
        
    Raises:
        FileNotFoundError: If Modal CLI is not installed
        Exception: For other deployment errors
    """
    try:
        print("🚀 Deploying Nobel embedder to Modal...")
        
        # Deploy using modal CLI with full output capture
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
    """
    Check if the app is deployed and running correctly.
    
    This function verifies that the deployed app is accessible and can
    respond to health check requests. It uses Modal's App.lookup API
    to connect to the deployed service.
    
    Returns:
        bool: True if app is healthy, False otherwise
        
    Raises:
        modal.exception.NotFoundError: If app is not deployed
        Exception: For other connection or health check errors
    """
    try:
        print("🔍 Checking app status...")
        stub = modal.App.lookup("nobel-embedder")
        
        # Try to call health check using the correct Modal API
        # This verifies the app is deployed and functions are accessible
        health_check = stub.function("health_check")
        result = health_check.remote()
        
        print(f"✅ App is running: {result}")
        return True
        
    except modal.exception.NotFoundError:
        print("❌ App not found - needs to be deployed")
        return False
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def main():
    """
    Main deployment function that orchestrates the deployment process.
    
    This function:
    1. Checks if the app is already deployed and healthy
    2. Deploys the app if needed
    3. Verifies the deployment was successful
    4. Provides helpful feedback and next steps
    
    The deployment process includes:
    - Pre-deployment status check
    - Modal CLI deployment
    - Post-deployment verification
    - Error handling and user guidance
    """
    print("🎯 Nobel Embedder Service Deployment")
    print("=" * 40)
    
    # Step 1: Check if app already exists and is healthy
    if check_app_status():
        print("\n✅ App is already deployed and running!")
        print("\n📋 Next steps:")
        print("   - Test the service: modal run modal_embedder.py")
        print("   - Use in production: stub.function('embed_query').remote('query')")
        return
    
    # Step 2: Deploy the app
    print("\n🚀 Starting deployment...")
    if deploy_app():
        print("\n⏳ Waiting for deployment to stabilize...")
        time.sleep(10)  # Allow time for deployment to complete
        
        # Step 3: Verify deployment was successful
        if check_app_status():
            print("\n🎉 Deployment verified successfully!")
            print("\n📋 Next steps:")
            print("   - Test the service: modal run modal_embedder.py")
            print("   - Use in production: stub.function('embed_query').remote('query')")
        else:
            print("\n⚠️  Deployment may have issues. Check logs with:")
            print("   modal logs nobel-embedder")
            print("\n💡 Try testing manually:")
            print("   modal run modal_embedder.py")
    else:
        print("\n❌ Deployment failed. Check the error messages above.")
        print("\n💡 Troubleshooting:")
        print("   - Ensure Modal CLI is installed: pip install modal")
        print("   - Check Modal authentication: modal setup")
        print("   - Verify modal_embedder.py exists and is valid")

if __name__ == "__main__":
    """
    Script entry point.
    
    This script can be run directly to deploy the Modal embedder service.
    It provides a complete deployment workflow with error handling and
    user guidance.
    """
    main() 